import unittest

import testing_db  # noqa: F401  (import bootstraps the ghost test DB)
from db import DBManager

class TestAddressLogic(unittest.TestCase):
    def setUp(self):
        self.db = DBManager()
        cur = self.db.conn.cursor()

        # orders must go before users (an order can reference one of this
        # user's addresses, and that FK isn't cascading) - see tearDown too
        cur.execute("DELETE FROM orders WHERE user_id IN (SELECT id FROM users WHERE username = 'address_user')")
        cur.execute("DELETE FROM users WHERE username = 'address_user'")
        self.db.conn.commit()

        cur.execute(
            "INSERT INTO users (username, password, role, email, phone_number) VALUES (%s, %s, %s, %s, %s)",
            ("address_user", "pass", "CUSTOMER", "address@test.com", "1010101010")
        )
        self.user_id = cur.lastrowid
        cur.close()

    def tearDown(self):
        cur = self.db.conn.cursor()
        cur.execute("DELETE FROM orders WHERE user_id = %s", (self.user_id,))
        cur.execute("DELETE FROM users WHERE id = %s", (self.user_id,))
        self.db.conn.commit()
        self.db.close()

    def test_get_addresses_empty(self):
        result = self.db.addresses.get_addresses(self.user_id)
        self.assertEqual(result, [])

    def test_add_address_success(self):
        success = self.db.addresses.add_address(self.user_id, "123 Test Street")
        self.assertTrue(success)

    def test_add_and_retrieve_address(self):
        self.db.addresses.add_address(self.user_id, "456 Mock Blvd")

        result = self.db.addresses.get_addresses(self.user_id)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["address"], "456 Mock Blvd")
        self.assertIn("id", result[0])

    def test_delete_address_success(self):
        self.db.addresses.add_address(self.user_id, "789 Deletable Ln")
        address_id = self.db.addresses.get_addresses(self.user_id)[0]["id"]

        success, error = self.db.addresses.delete_address(self.user_id, address_id)

        self.assertTrue(success)
        self.assertIsNone(error)
        self.assertEqual(self.db.addresses.get_addresses(self.user_id), [])

    def test_delete_address_referenced_by_order_fails_with_friendly_message(self):
        self.db.addresses.add_address(self.user_id, "1 Order Blocked Way")
        address_id = self.db.addresses.get_addresses(self.user_id)[0]["id"]

        cur = self.db.conn.cursor()
        cur.execute(
            "INSERT INTO orders (user_id, address_id, price, payment_method, status) "
            "VALUES (%s, %s, 12.00, 'CASH', 'PENDING')",
            (self.user_id, address_id),
        )
        cur.close()

        success, error = self.db.addresses.delete_address(self.user_id, address_id)

        self.assertFalse(success)
        self.assertIn("used by an existing order", error)
        # the address must still be there since the delete was rejected
        self.assertEqual(len(self.db.addresses.get_addresses(self.user_id)), 1)

if __name__ == '__main__':
    unittest.main()