import unittest
from unittest.mock import MagicMock, patch

from services.delivery import Delivery


class TestListRestaurantsForDeliveryUnit(unittest.TestCase):
    def test_maps_id_and_name(self):
        db = MagicMock()
        db.delivery.get_restaurants_for_delivery.return_value = [(1, "Pizzaria"), (2, "Souvlatzidiko")]
        service = Delivery(db)

        result = service.list_restaurants_for_delivery(9)

        self.assertEqual(result, [
            {"id": 1, "text": "Pizzaria"},
            {"id": 2, "text": "Souvlatzidiko"},
        ])


class TestGenerateInviteCodeUnit(unittest.TestCase):
    @patch("services.delivery.generate_code", return_value="ABC12345")
    def test_returns_generated_code_on_success(self, _mock_gen):
        db = MagicMock()
        db.delivery.create_invite_code.return_value = True
        service = Delivery(db)

        code = service.generate_invite_code(1, 5)

        self.assertEqual(code, "ABC12345")
        db.delivery.create_invite_code.assert_called_once_with(1, "ABC12345", 5)

    def test_returns_none_on_db_failure(self):
        db = MagicMock()
        db.delivery.create_invite_code.return_value = False
        service = Delivery(db)

        self.assertIsNone(service.generate_invite_code(1, 5))


class TestRedeemInviteCodeUnit(unittest.TestCase):
    def setUp(self):
        self.db = MagicMock()
        self.service = Delivery(self.db)

    def test_rejects_empty_code_without_touching_db(self):
        restaurant_id, error = self.service.redeem_invite_code("   ", 9)

        self.assertIsNone(restaurant_id)
        self.assertIn("Enter a code", error)
        self.db.delivery.find_invite_code.assert_not_called()

    def test_unknown_code_returns_not_found_error(self):
        self.db.delivery.find_invite_code.return_value = None

        restaurant_id, error = self.service.redeem_invite_code("BADCODE", 9)

        self.assertIsNone(restaurant_id)
        self.assertIn("doesn't exist", error)

    def test_already_used_code_returns_distinct_error(self):
        self.db.delivery.find_invite_code.return_value = (1, 7, 99)

        restaurant_id, error = self.service.redeem_invite_code("GOODCODE", 9)

        self.assertIsNone(restaurant_id)
        self.assertIn("already been used", error)

    def test_already_registered_returns_error_without_writing(self):
        self.db.delivery.find_invite_code.return_value = (1, 7, None)
        self.db.delivery.is_delivery_linked.return_value = True

        restaurant_id, error = self.service.redeem_invite_code("GOODCODE", 9)

        self.assertIsNone(restaurant_id)
        self.assertIn("already registered", error)
        self.db.delivery.redeem_invite_code_atomic.assert_not_called()

    def test_successful_redemption_returns_restaurant_id(self):
        self.db.delivery.find_invite_code.return_value = (1, 7, None)
        self.db.delivery.is_delivery_linked.return_value = False
        self.db.delivery.redeem_invite_code_atomic.return_value = True

        restaurant_id, error = self.service.redeem_invite_code("goodcode", 9)

        self.assertEqual(restaurant_id, 7)
        self.assertIsNone(error)
        self.db.delivery.redeem_invite_code_atomic.assert_called_once_with(1, 7, 9)

    def test_code_is_normalized_to_uppercase_and_stripped(self):
        self.db.delivery.find_invite_code.return_value = None

        self.service.redeem_invite_code("  abc123  ", 9)

        self.db.delivery.find_invite_code.assert_called_once_with("ABC123")

    def test_race_lost_returns_friendly_error(self):
        self.db.delivery.find_invite_code.return_value = (1, 7, None)
        self.db.delivery.is_delivery_linked.return_value = False
        self.db.delivery.redeem_invite_code_atomic.return_value = False

        restaurant_id, error = self.service.redeem_invite_code("GOODCODE", 9)

        self.assertIsNone(restaurant_id)
        self.assertIn("just used by someone else", error)


if __name__ == "__main__":
    unittest.main()
