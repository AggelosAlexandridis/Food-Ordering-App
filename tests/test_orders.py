import unittest

import testing_db
from db import DBManager
from services import ServiceManager

class TestOrderLogic(unittest.TestCase):
    def setUp(self):
        self.db = DBManager()
        self.services = ServiceManager(self.db)
        cur = self.db.conn.cursor()

        cur.execute("DELETE FROM orders WHERE user_id IN (SELECT id FROM users WHERE username = 'order_user')")
        cur.execute("DELETE FROM users WHERE username = 'order_user'")
        self.db.conn.commit()

        cur.execute(
            "INSERT INTO users (username, password, role, email, phone_number) VALUES (%s, %s, %s, %s, %s)",
            ("order_user", "pass", "CUSTOMER", "order@test.com", "2020202020")
        )
        self.user_id = cur.lastrowid
        
        cur.execute("INSERT INTO addresses (user_id, address) VALUES (%s, %s)", (self.user_id, "789 Checkout Ave"))
        self.address_id = cur.lastrowid
        cur.close()

    def tearDown(self):
        cur = self.db.conn.cursor()
        cur.execute("DELETE FROM orders WHERE user_id = %s", (self.user_id,))
        cur.execute("DELETE FROM users WHERE id = %s", (self.user_id,))
        self.db.conn.commit()
        self.db.close()

    def test_get_user_orders_empty(self):
        result = self.db.orders.get_user_orders(self.user_id)
        self.assertEqual(result, [])

    def test_checkout_fails_without_wallet(self):
        success, error = self.services.orders.checkout(
            self.user_id, None, self.address_id, "CARD", 25.50, 0, None
        )
        self.assertFalse(success)
        self.assertIn("Wallet not found", error)

    def test_checkout_success(self):
        cur = self.db.conn.cursor()
        cur.execute("INSERT INTO wallets (user_id, balance) VALUES (%s, %s)", (self.user_id, 100.0))
        cur.close()

        success, error = self.services.orders.checkout(
            self.user_id, None, self.address_id, "CARD", 25.50, 0, None
        )
        self.assertTrue(success)
        self.assertIsNone(error)

    def test_checkout_cash_succeeds_without_wallet(self):
        success, error = self.services.orders.checkout(
            self.user_id, None, self.address_id, "CASH", 25.50, 0, None
        )
        self.assertTrue(success)
        self.assertIsNone(error)

    def test_checkout_and_list_user_orders(self):
        cur = self.db.conn.cursor()
        cur.execute("INSERT INTO wallets (user_id, balance) VALUES (%s, %s)", (self.user_id, 100.0))
        cur.close()

        self.services.orders.checkout(self.user_id, None, self.address_id, "CARD", 42.00, 0, None)

        orders = self.services.orders.list_user_orders(self.user_id)
        self.assertEqual(len(orders), 1)
        self.assertIn("Total: 42.00€", orders[0]["text"])
        self.assertIn("Status: PENDING", orders[0]["text"])

if __name__ == '__main__':
    unittest.main()
