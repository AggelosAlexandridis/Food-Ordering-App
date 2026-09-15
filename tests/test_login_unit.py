import unittest
from unittest.mock import MagicMock

from db.login import Login


class TestFindCredentialsUnit(unittest.TestCase):
    def setUp(self):
        self.conn = MagicMock()
        self.cursor = self.conn.cursor.return_value.__enter__.return_value
        self.login = Login(self.conn)

    def test_returns_row_when_found(self):
        self.cursor.fetchone.return_value = (1, "CUSTOMER", "some-stored-hash")

        result = self.login.find_credentials("alice")

        self.assertEqual(result, (1, "CUSTOMER", "some-stored-hash"))

    def test_returns_none_when_not_found(self):
        self.cursor.fetchone.return_value = None

        self.assertIsNone(self.login.find_credentials("nobody"))

    def test_query_checks_username_or_email(self):
        self.cursor.fetchone.return_value = None

        self.login.find_credentials("alice@test.com")

        query, params = self.cursor.execute.call_args.args
        self.assertIn("username=%s OR email=%s", query)
        self.assertEqual(params, ("alice@test.com", "alice@test.com"))


class TestUniquenessChecksUnit(unittest.TestCase):
    def setUp(self):
        self.conn = MagicMock()
        self.cursor = self.conn.cursor.return_value.__enter__.return_value
        self.login = Login(self.conn)

    def test_username_exists_true(self):
        self.cursor.fetchone.return_value = (1,)
        self.assertTrue(self.login.username_exists("alice"))

    def test_username_exists_false(self):
        self.cursor.fetchone.return_value = None
        self.assertFalse(self.login.username_exists("alice"))

    def test_email_exists(self):
        self.cursor.fetchone.return_value = (1,)
        self.assertTrue(self.login.email_exists("a@test.com"))

    def test_phone_exists(self):
        self.cursor.fetchone.return_value = None
        self.assertFalse(self.login.phone_exists("12345"))


class TestCreateUserUnit(unittest.TestCase):
    def setUp(self):
        self.conn = MagicMock()
        self.cursor = self.conn.cursor.return_value.__enter__.return_value
        self.login = Login(self.conn)

    def test_inserts_hashed_password_and_creates_wallet(self):
        self.cursor.lastrowid = 42

        user_id = self.login.create_user("alice", "hashed-value", "a@test.com", "12345")

        self.assertEqual(user_id, 42)
        self.conn.commit.assert_called_once()

        insert_call = next(
            c for c in self.cursor.execute.call_args_list if "INSERT INTO users" in c.args[0]
        )
        params = insert_call.args[1]
        self.assertIn("hashed-value", params)

        wallet_call = next(
            c for c in self.cursor.execute.call_args_list if "INSERT INTO wallets" in c.args[0]
        )
        self.assertEqual(wallet_call.args[1], (42,))

    def test_db_error_rolls_back_and_returns_none(self):
        self.cursor.execute.side_effect = Exception("boom")

        result = self.login.create_user("alice", "hashed-value", "a@test.com", "12345")

        self.assertIsNone(result)
        self.conn.rollback.assert_called_once()


if __name__ == "__main__":
    unittest.main()
