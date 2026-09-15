import unittest
from unittest.mock import MagicMock

from services.users import Users


class TestGetProfileUnit(unittest.TestCase):
    def test_maps_row_to_dict(self):
        db = MagicMock()
        db.users.get_profile_row.return_value = ("alice", "Alice Doe", "alice@test.com", "1234567890")
        service = Users(db)

        result = service.get_profile(1)

        self.assertEqual(result, {
            "username": "alice",
            "name": "Alice Doe",
            "email": "alice@test.com",
            "phone_number": "1234567890",
        })

    def test_returns_none_when_missing(self):
        db = MagicMock()
        db.users.get_profile_row.return_value = None
        service = Users(db)

        self.assertIsNone(service.get_profile(999999))


class TestGetRestaurantIdUnit(unittest.TestCase):
    def test_delegates_to_repository(self):
        db = MagicMock()
        db.users.get_restaurant_id.return_value = 3
        service = Users(db)

        self.assertEqual(service.get_restaurant_id(1), 3)


class TestUpdateNameUnit(unittest.TestCase):
    def setUp(self):
        self.db = MagicMock()
        self.service = Users(self.db)

    def test_rejects_empty_name_without_touching_db(self):
        success, error = self.service.update_name(1, "   ")

        self.assertFalse(success)
        self.assertIn("cannot be empty", error)
        self.db.users.update_name.assert_not_called()

    def test_strips_and_saves_valid_name(self):
        self.db.users.update_name.return_value = True

        success, error = self.service.update_name(1, "  New Name  ")

        self.assertTrue(success)
        self.assertIsNone(error)
        self.db.users.update_name.assert_called_once_with(1, "New Name")

    def test_db_failure_returns_friendly_error(self):
        self.db.users.update_name.return_value = False

        success, error = self.service.update_name(1, "New Name")

        self.assertFalse(success)
        self.assertIn("Error saving name", error)


if __name__ == "__main__":
    unittest.main()
