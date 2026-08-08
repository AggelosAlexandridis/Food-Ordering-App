import unittest

import testing_db  # noqa: F401  (import bootstraps the ghost test DB)
from db import DBManager


class TestWallet(unittest.TestCase):
    def setUp(self):
        self.db = DBManager()
        cur = self.db.conn.cursor()
        cur.execute("DELETE FROM users WHERE username = 'wallet_add_user'")
        self.db.conn.commit()
        cur.close()

    def tearDown(self):
        cur = self.db.conn.cursor()
        cur.execute("DELETE FROM users WHERE username = 'wallet_add_user'")
        self.db.conn.commit()
        self.db.close()

    def test_add_money_to_wallet(self):
        cur = self.db.conn.cursor()
        cur.execute(
            "INSERT INTO users (username, password, role, email, phone_number) VALUES (%s, %s, %s, %s, %s)",
            ("wallet_add_user", "pass", "CUSTOMER", "walletadd@test.com", "1112223333"),
        )
        user_id = cur.lastrowid
        cur.execute("INSERT INTO wallets (user_id, balance) VALUES (%s, %s)", (user_id, 0.0))
        cur.close()

        self.db.wallet.update_balance(user_id, 100.0)

        result = self.db.wallet.get_balance(user_id)
        self.assertEqual(result, 100.0)


if __name__ == "__main__":
    unittest.main()
