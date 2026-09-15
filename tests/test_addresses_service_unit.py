import unittest
from unittest.mock import MagicMock

import mariadb

from services.addresses import Addresses


class TestListAddressesUnit(unittest.TestCase):
    def setUp(self):
        self.db = MagicMock()
        self.service = Addresses(self.db)

    def test_maps_rows_to_display_dicts(self):
        self.db.addresses.get_addresses.return_value = [(1, "123 Main St"), (2, "456 Oak Ave")]

        result = self.service.list_addresses(7)

        self.assertEqual(result, [
            {"id": 1, "address": "123 Main St", "text": "123 Main St"},
            {"id": 2, "address": "456 Oak Ave", "text": "456 Oak Ave"},
        ])

    def test_empty(self):
        self.db.addresses.get_addresses.return_value = []

        self.assertEqual(self.service.list_addresses(7), [])


class TestAddAddressUnit(unittest.TestCase):
    def setUp(self):
        self.db = MagicMock()
        self.service = Addresses(self.db)

    def test_rejects_empty_text_without_touching_db(self):
        success, error = self.service.add_address(1, "   ")

        self.assertFalse(success)
        self.assertEqual(error, "Address field cannot be empty!")
        self.db.addresses.add_address.assert_not_called()

    def test_strips_and_saves_valid_text(self):
        self.db.addresses.add_address.return_value = True

        success, error = self.service.add_address(1, "  789 Pine Rd  ")

        self.assertTrue(success)
        self.assertIsNone(error)
        self.db.addresses.add_address.assert_called_once_with(1, "789 Pine Rd")

    def test_db_failure_returns_friendly_error(self):
        self.db.addresses.add_address.return_value = False

        success, error = self.service.add_address(1, "789 Pine Rd")

        self.assertFalse(success)
        self.assertIn("Error saving", error)


class TestDeleteAddressUnit(unittest.TestCase):
    def setUp(self):
        self.db = MagicMock()
        self.service = Addresses(self.db)

    def test_success(self):
        self.db.addresses.delete_address.return_value = True

        success, error = self.service.delete_address(1, 9)

        self.assertTrue(success)
        self.assertIsNone(error)

    def test_not_found(self):
        self.db.addresses.delete_address.return_value = False

        success, error = self.service.delete_address(1, 9)

        self.assertFalse(success)
        self.assertIn("not found", error)

    def test_integrity_error_translated_to_friendly_message(self):
        self.db.addresses.delete_address.side_effect = mariadb.IntegrityError("FK fails")

        success, error = self.service.delete_address(1, 9)

        self.assertFalse(success)
        self.assertIn("used by an existing order", error)


if __name__ == "__main__":
    unittest.main()
