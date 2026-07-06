import unittest
from db import DBManager

class TestWalletAndCart(unittest.TestCase):
    def setUp(self):
        self.db = DBManager()
        cur = self.db.conn.cursor()
        
        cur.execute("DELETE FROM users WHERE username IN ('wallet_test_user', 'wallet_upd_user')")
        cur.execute("DELETE FROM restaurants WHERE name = 'Cart Rest'")
        self.db.conn.commit()
        cur.close()

    def tearDown(self):
        cur = self.db.conn.cursor()
        cur.execute("DELETE FROM users WHERE username IN ('wallet_test_user', 'wallet_upd_user')")
        cur.execute("DELETE FROM restaurants WHERE name = 'Cart Rest'")
        self.db.conn.commit()
        self.db.close()

    def test_get_balance_for_nonexistent_user_returns_none(self):
        result = self.db.get_balance(999999)
        self.assertIsNone(result)

    def test_get_balance_returns_float(self):
        cur = self.db.conn.cursor()
        cur.execute(
            "INSERT INTO users (username, password, role, email, phone_number) VALUES (%s, %s, %s, %s, %s)",
            ("wallet_test_user", "pass", "CUSTOMER", "wallet@test.com", "4445556666")
        )
        user_id = cur.lastrowid
        cur.execute("INSERT INTO wallets (user_id, balance) VALUES (%s, %s)", (user_id, 42.5))
        cur.close()

        result = self.db.get_balance(user_id)
        self.assertEqual(result, 42.5)

    def test_update_balance_success(self):
        cur = self.db.conn.cursor()
        cur.execute(
            "INSERT INTO users (username, password, role, email, phone_number) VALUES (%s, %s, %s, %s, %s)",
            ("wallet_upd_user", "pass", "CUSTOMER", "upd@test.com", "7778889999")
        )
        user_id = cur.lastrowid
        cur.execute("INSERT INTO wallets (user_id, balance) VALUES (%s, %s)", (user_id, 10.0))
        cur.close()

        success = self.db.update_balance(user_id, 50.0)
        self.assertTrue(success)
        
        new_balance = self.db.get_balance(user_id)
        self.assertEqual(new_balance, 50.0)

    def test_get_cart_items_empty_cart(self):
        result = self.db.get_cart_items([])
        self.assertEqual(result, [])

    def test_get_cart_items_calculates_total_correctly(self):
        cur = self.db.conn.cursor()
        cur.execute("INSERT INTO restaurants (name) VALUES ('Cart Rest')")
        rest_id = cur.lastrowid
        cur.execute(
            "INSERT INTO food (name, price, restaurant_id) VALUES (%s, %s, %s)",
            ("Test Pizza", 10.0, rest_id)
        )
        food_id = cur.lastrowid
        cur.close()

        cart = [{"id": food_id, "quantity": 3}]
        result = self.db.get_cart_items(cart)

        self.assertEqual(len(result), 1)
        self.assertIn("x3", result[0]["text"])
        self.assertEqual(result[0]["price"], 30.0)

if __name__ == '__main__':
    unittest.main()