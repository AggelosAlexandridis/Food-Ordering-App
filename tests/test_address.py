import unittest
from db import DBManager

class TestAddressLogic(unittest.TestCase):
    def setUp(self):
        self.db = DBManager()
        cur = self.db.conn.cursor()
        
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
        cur.execute("DELETE FROM users WHERE id = %s", (self.user_id,))
        self.db.conn.commit()
        self.db.close()

    def test_get_addresses_empty(self):
        result = self.db.get_addresses(self.user_id)
        self.assertEqual(result, [])

    def test_add_address_success(self):
        success = self.db.add_address(self.user_id, "123 Test Street")
        self.assertTrue(success)

    def test_add_and_retrieve_address(self):
        self.db.add_address(self.user_id, "456 Mock Blvd")
        
        result = self.db.get_addresses(self.user_id)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["address"], "456 Mock Blvd")
        self.assertIn("id", result[0])

if __name__ == '__main__':
    unittest.main()