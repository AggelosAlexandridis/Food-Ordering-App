import unittest
from db import DBManager

class TestOrderLogic(unittest.TestCase):
    def setUp(self):
        self.db = DBManager()
        cur = self.db.conn.cursor()
        
        # 1. Clean up from any previous test failures. (Orders FIRST!)
        cur.execute("DELETE FROM orders WHERE user_id IN (SELECT id FROM users WHERE username = 'order_user')")
        cur.execute("DELETE FROM users WHERE username = 'order_user'")
        self.db.conn.commit()

        # 2. Setup user and address
        cur.execute(
            "INSERT INTO users (username, password, role, email, phone_number) VALUES (%s, %s, %s, %s, %s)",
            ("order_user", "pass", "CUSTOMER", "order@test.com", "2020202020")
        )
        self.user_id = cur.lastrowid
        
        cur.execute("INSERT INTO addresses (user_id, address) VALUES (%s, %s)", (self.user_id, "789 Checkout Ave"))
        self.address_id = cur.lastrowid
        cur.close()

    def tearDown(self):
        # 3. Clean up explicitly (Orders FIRST!)
        cur = self.db.conn.cursor()
        cur.execute("DELETE FROM orders WHERE user_id = %s", (self.user_id,))
        cur.execute("DELETE FROM users WHERE id = %s", (self.user_id,))
        self.db.conn.commit()
        self.db.close()

    def test_get_user_orders_empty(self):
        result = self.db.get_user_orders(self.user_id)
        self.assertEqual(result, [])

    def test_submit_order_fails_without_wallet(self):
        # User exists but no wallet was created
        success = self.db.submit_order(self.user_id, self.address_id, 25.50)
        self.assertFalse(success)

    def test_submit_order_success(self):
        # Create a wallet for the user first
        cur = self.db.conn.cursor()
        cur.execute("INSERT INTO wallets (user_id, balance) VALUES (%s, %s)", (self.user_id, 100.0))
        cur.close()

        success = self.db.submit_order(self.user_id, self.address_id, 25.50)
        self.assertTrue(success)

    def test_submit_and_get_user_orders(self):
        # Setup wallet & create an order
        cur = self.db.conn.cursor()
        cur.execute("INSERT INTO wallets (user_id, balance) VALUES (%s, %s)", (self.user_id, 100.0))
        cur.close()
        
        self.db.submit_order(self.user_id, self.address_id, 42.00)

        # Retrieve the order
        orders = self.db.get_user_orders(self.user_id)
        self.assertEqual(len(orders), 1)
        self.assertIn("Total: 42.00€", orders[0]["text"])
        self.assertIn("Status: PENDING", orders[0]["text"])

if __name__ == '__main__':
    unittest.main()