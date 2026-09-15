import unittest
from unittest.mock import MagicMock

from db.delivery import Delivery


class TestGetRestaurantsForDeliveryUnit(unittest.TestCase):
    def setUp(self):
        self.conn = MagicMock()
        self.cursor = self.conn.cursor.return_value.__enter__.return_value
        self.delivery = Delivery(self.conn)

    def test_returns_raw_rows(self):
        self.cursor.fetchall.return_value = [(1, "Pizzaria"), (2, "Souvlatzidiko")]

        result = self.delivery.get_restaurants_for_delivery(9)

        self.assertEqual(result, [(1, "Pizzaria"), (2, "Souvlatzidiko")])


class TestCreateInviteCodeUnit(unittest.TestCase):
    def setUp(self):
        self.conn = MagicMock()
        self.cursor = self.conn.cursor.return_value.__enter__.return_value
        self.delivery = Delivery(self.conn)

    def test_commits_and_returns_true(self):
        result = self.delivery.create_invite_code(1, "ABC12345", 5)

        self.assertTrue(result)
        self.conn.commit.assert_called_once()
        query, params = self.cursor.execute.call_args.args
        self.assertIn("INSERT INTO restaurant_invite_codes", query)
        self.assertEqual(params, (1, "ABC12345", 5))

    def test_db_error_rolls_back_and_returns_false(self):
        self.cursor.execute.side_effect = Exception("boom")

        result = self.delivery.create_invite_code(1, "ABC12345", 5)

        self.assertFalse(result)
        self.conn.rollback.assert_called_once()


class TestFindInviteCodeUnit(unittest.TestCase):
    def setUp(self):
        self.conn = MagicMock()
        self.cursor = self.conn.cursor.return_value.__enter__.return_value
        self.delivery = Delivery(self.conn)

    def test_returns_row_when_found(self):
        self.cursor.fetchone.return_value = (1, 7, None)

        self.assertEqual(self.delivery.find_invite_code("GOODCODE"), (1, 7, None))

    def test_returns_none_when_missing(self):
        self.cursor.fetchone.return_value = None

        self.assertIsNone(self.delivery.find_invite_code("BADCODE"))


class TestIsDeliveryLinkedUnit(unittest.TestCase):
    def setUp(self):
        self.conn = MagicMock()
        self.cursor = self.conn.cursor.return_value.__enter__.return_value
        self.delivery = Delivery(self.conn)

    def test_true_when_linked(self):
        self.cursor.fetchone.return_value = (1,)
        self.assertTrue(self.delivery.is_delivery_linked(9, 7))

    def test_false_when_not_linked(self):
        self.cursor.fetchone.return_value = None
        self.assertFalse(self.delivery.is_delivery_linked(9, 7))


class TestRedeemInviteCodeAtomicUnit(unittest.TestCase):
    def setUp(self):
        self.conn = MagicMock()
        self.cursor = self.conn.cursor.return_value.__enter__.return_value
        self.delivery = Delivery(self.conn)

    def test_successful_redemption_links_and_commits(self):
        self.cursor.rowcount = 1

        result = self.delivery.redeem_invite_code_atomic(1, 7, 9)

        self.assertTrue(result)
        self.conn.commit.assert_called_once()

    def test_race_lost_rolls_back_and_returns_false(self):
        self.cursor.rowcount = 0

        result = self.delivery.redeem_invite_code_atomic(1, 7, 9)

        self.assertFalse(result)
        self.conn.rollback.assert_called_once()
        self.conn.commit.assert_not_called()

    def test_db_error_rolls_back_and_returns_false(self):
        self.cursor.execute.side_effect = Exception("boom")

        result = self.delivery.redeem_invite_code_atomic(1, 7, 9)

        self.assertFalse(result)
        self.conn.rollback.assert_called_once()


if __name__ == "__main__":
    unittest.main()
