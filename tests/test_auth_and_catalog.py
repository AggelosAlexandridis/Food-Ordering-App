import unittest
from db import DBManager

class TestAuthAndCatalog(unittest.TestCase):
    def setUp(self):
        self.db = DBManager()
        self.db.conn.autocommit = False  

    def tearDown(self):
        self.db.conn.rollback()
        self.db.close()

    def test_check_login_invalid_credentials_returns_none(self):
        result = self.db.check_login("fake_user_99", "wrongpass")
        self.assertIsNone(result)

    def test_check_login_valid_user(self):
        cur = self.db.conn.cursor()
        cur.execute(
            "INSERT INTO users (username, password, role, email, phone_number) VALUES (%s, %s, %s, %s, %s)",
            ("auth_test_user", "test_pass", "CUSTOMER", "auth@test.com", "1112223333")
        )
        cur.close()

        result = self.db.check_login("auth_test_user", "test_pass")
        self.assertIsNotNone(result)
        self.assertEqual(result[1].upper(), "CUSTOMER")

    def test_get_restaurants_returns_list(self):
        result = self.db.get_restaurants()
        self.assertIsInstance(result, list)
        if result:
            self.assertIn("id", result[0])
            self.assertIn("text", result[0])

    def test_get_menu_for_nonexistent_restaurant_returns_empty(self):
        result = self.db.get_menu(999999)
        self.assertEqual(result, [])

    def test_get_menu_returns_items(self):
        cur = self.db.conn.cursor()
        cur.execute("INSERT INTO restaurants (name) VALUES ('Test Rest')")
        rest_id = cur.lastrowid
        cur.execute(
            "INSERT INTO food (name, price, restaurant_id) VALUES (%s, %s, %s)",
            ("Test Burger", 5.50, rest_id)
        )
        cur.close()

        result = self.db.get_menu(rest_id)
        self.assertEqual(len(result), 1)
        self.assertIn("Test Burger", result[0]["text"])

if __name__ == '__main__':
    unittest.main()