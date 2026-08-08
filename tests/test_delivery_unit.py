import unittest
from unittest.mock import MagicMock, patch

from db.delivery import Delivery


class TestGetRestaurantsForDeliveryUnit(unittest.TestCase):
    def setUp(self):
        self.conn = MagicMock()
        self.cursor = self.conn.cursor.return_value.__enter__.return_value
        self.delivery = Delivery(self.conn)

    def test_maps_id_and_name(self):
        self.cursor.fetchall.return_value = [(1, "Pizzaria"), (2, "Souvlatzidiko")]

        result = self.delivery.get_restaurants_for_delivery(9)

        self.assertEqual(result, [
            {"id": 1, "text": "Pizzaria"},
            {"id": 2, "text": "Souvlatzidiko"},
        ])


class TestGenerateInviteCodeUnit(unittest.TestCase):
    def setUp(self):
        self.conn = MagicMock()
        self.cursor = self.conn.cursor.return_value.__enter__.return_value
        self.delivery = Delivery(self.conn)

    @patch("db.delivery.generate_code", return_value="ABC12345")
    def test_returns_generated_code_and_commits(self, _mock_gen):
        code = self.delivery.generate_invite_code(1, 5)

        self.assertEqual(code, "ABC12345")
        self.conn.commit.assert_called_once()

    def test_db_error_rolls_back_and_returns_none(self):
        self.cursor.execute.side_effect = Exception("boom")

        code = self.delivery.generate_invite_code(1, 5)

        self.assertIsNone(code)
        self.conn.rollback.assert_called_once()


class TestRedeemInviteCodeUnit(unittest.TestCase):
    def setUp(self):
        self.conn = MagicMock()
        self.cursor = self.conn.cursor.return_value.__enter__.return_value
        self.delivery = Delivery(self.conn)

    def test_unknown_code_returns_not_found_error(self):
        self.cursor.fetchone.return_value = None

        restaurant_id, error = self.delivery.redeem_invite_code("BADCODE", 9)

        self.assertIsNone(restaurant_id)
        self.assertIn("doesn't exist", error)
        self.conn.commit.assert_not_called()

    def test_already_used_code_returns_distinct_error(self):
        # id=1, restaurant_id=7, used_by=99 (already redeemed by someone else)
        self.cursor.fetchone.return_value = (1, 7, 99)

        restaurant_id, error = self.delivery.redeem_invite_code("GOODCODE", 9)

        self.assertIsNone(restaurant_id)
        self.assertIn("already been used", error)
        self.conn.commit.assert_not_called()

    def test_already_registered_returns_error_without_writing(self):
        # first lookup: code found, unused; second: already-linked check finds a row
        self.cursor.fetchone.side_effect = [(1, 7, None), (1,)]

        restaurant_id, error = self.delivery.redeem_invite_code("GOODCODE", 9)

        self.assertIsNone(restaurant_id)
        self.assertIn("already registered", error)
        self.conn.commit.assert_not_called()

    def test_successful_redemption_links_and_commits(self):
        self.cursor.fetchone.side_effect = [(1, 7, None), None]  # found+unused, not yet linked
        self.cursor.rowcount = 1  # the used_by UPDATE matched a row

        restaurant_id, error = self.delivery.redeem_invite_code("goodcode", 9)

        self.assertEqual(restaurant_id, 7)
        self.assertIsNone(error)
        self.conn.commit.assert_called_once()

    def test_code_is_normalized_to_uppercase_and_stripped(self):
        self.cursor.fetchone.return_value = None

        self.delivery.redeem_invite_code("  abc123  ", 9)

        query, params = self.cursor.execute.call_args.args
        self.assertEqual(params, ("ABC123",))

    def test_race_where_code_used_between_lookup_and_update_rolls_back(self):
        # code found and not-yet-linked at check time, but the guarded UPDATE
        # matches zero rows because another request won the race first
        self.cursor.fetchone.side_effect = [(1, 7, None), None]
        self.cursor.rowcount = 0

        restaurant_id, error = self.delivery.redeem_invite_code("GOODCODE", 9)

        self.assertIsNone(restaurant_id)
        self.assertIn("just used by someone else", error)
        self.conn.commit.assert_not_called()


if __name__ == "__main__":
    unittest.main()
