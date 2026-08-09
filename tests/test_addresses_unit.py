import unittest
from unittest.mock import MagicMock

import mariadb

from db.addresses import Addresses


class TestAddressesUnit(unittest.TestCase):
    """Pure unit tests: the DB connection/cursor are mocked, no real DB is touched."""

    def setUp(self):
        self.conn = MagicMock()
        self.cursor = self.conn.cursor.return_value.__enter__.return_value
        self.addresses = Addresses(self.conn)

    def test_get_addresses_maps_rows_to_dicts(self):
        self.cursor.fetchall.return_value = [(1, "123 Main St"), (2, "456 Oak Ave")]

        result = self.addresses.get_addresses(7)

        self.assertEqual(result, [
            {"id": 1, "address": "123 Main St", "text": "123 Main St"},
            {"id": 2, "address": "456 Oak Ave", "text": "456 Oak Ave"},
        ])

    def test_get_addresses_empty(self):
        self.cursor.fetchall.return_value = []

        self.assertEqual(self.addresses.get_addresses(7), [])

    def test_add_address_commits_and_returns_true(self):
        result = self.addresses.add_address(1, "789 Pine Rd")

        self.assertTrue(result)
        self.conn.commit.assert_called_once()
        query, params = self.cursor.execute.call_args.args
        self.assertIn("INSERT INTO addresses", query)
        self.assertEqual(params, (1, "789 Pine Rd"))

    def test_add_address_rolls_back_on_db_error(self):
        self.cursor.execute.side_effect = Exception("constraint violation")

        result = self.addresses.add_address(1, "bad data")

        self.assertFalse(result)
        self.conn.rollback.assert_called_once()

    def test_delete_address_scopes_by_owner_and_id(self):
        self.cursor.rowcount = 1

        success, error = self.addresses.delete_address(user_id=1, address_id=9)

        self.assertTrue(success)
        self.assertIsNone(error)
        query, params = self.cursor.execute.call_args.args
        self.assertIn("WHERE id = %s AND user_id = %s", query)
        self.assertEqual(params, (9, 1))
        self.conn.commit.assert_called_once()

    def test_delete_address_not_found_rolls_back(self):
        self.cursor.rowcount = 0

        success, error = self.addresses.delete_address(1, 9)

        self.assertFalse(success)
        self.assertIn("not found", error)
        self.conn.rollback.assert_called_once()
        self.conn.commit.assert_not_called()

    def test_delete_address_referenced_by_order_returns_friendly_error(self):
        self.cursor.execute.side_effect = mariadb.IntegrityError("FK constraint fails")

        success, error = self.addresses.delete_address(1, 9)

        self.assertFalse(success)
        self.assertIn("used by an existing order", error)
        self.conn.rollback.assert_called_once()

    def test_delete_address_rolls_back_on_other_db_error(self):
        self.cursor.execute.side_effect = Exception("db error")

        success, error = self.addresses.delete_address(1, 9)

        self.assertFalse(success)
        self.assertIn("try again", error)
        self.conn.rollback.assert_called_once()


if __name__ == "__main__":
    unittest.main()
