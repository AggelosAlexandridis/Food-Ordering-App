import unittest
from unittest.mock import MagicMock, patch

from db.login import Login


class TestLoginUnit(unittest.TestCase):
    """Pure unit tests: the DB connection/cursor are mocked, no real DB is touched."""

    def setUp(self):
        self.conn = MagicMock()
        self.cursor = self.conn.cursor.return_value.__enter__.return_value
        self.login = Login(self.conn)

    @patch("db.login.verify_password", return_value=True)
    def test_valid_credentials_returns_id_and_role(self, _mock_verify):
        self.cursor.fetchone.return_value = (1, "CUSTOMER", "some-stored-hash")

        result = self.login.check_login("alice", "secret")

        self.assertEqual(result, [1, "CUSTOMER"])

    def test_unknown_username_returns_none_without_verifying(self):
        self.cursor.fetchone.return_value = None

        result = self.login.check_login("alice", "wrongpass")

        self.assertIsNone(result)

    @patch("db.login.verify_password", return_value=False)
    def test_wrong_password_returns_none(self, _mock_verify):
        self.cursor.fetchone.return_value = (1, "CUSTOMER", "some-stored-hash")

        result = self.login.check_login("alice", "wrongpass")

        self.assertIsNone(result)

    def test_login_query_checks_username_or_email(self):
        self.cursor.fetchone.return_value = None

        self.login.check_login("alice@test.com", "secret")

        query, params = self.cursor.execute.call_args.args
        self.assertIn("username=%s OR email=%s", query)
        self.assertEqual(params, ("alice@test.com", "alice@test.com"))

    @patch("db.login.verify_password", return_value=True)
    def test_verify_password_is_called_with_plaintext_and_stored_hash(self, mock_verify):
        self.cursor.fetchone.return_value = (7, "CHEF", "the-stored-hash")

        self.login.check_login("bob", "pw")

        mock_verify.assert_called_once_with("pw", "the-stored-hash")

    @patch("db.login.verify_password", return_value=True)
    def test_login_uses_a_single_cursor_context(self, _mock_verify):
        self.cursor.fetchone.return_value = (7, "CHEF", "hash")

        self.login.check_login("bob", "pw")

        self.conn.cursor.assert_called_once()
        self.cursor.execute.assert_called_once()


class TestRegisterHashesPasswordUnit(unittest.TestCase):
    def setUp(self):
        self.conn = MagicMock()
        self.cursor = self.conn.cursor.return_value.__enter__.return_value
        self.login = Login(self.conn)
        # no existing username/email/phone conflicts
        self.cursor.fetchone.return_value = None

    @patch("db.login.hash_password", return_value="hashed-value")
    def test_insert_stores_hashed_password_not_plaintext(self, _mock_hash):
        self.login.register("alice", "plaintext-pw", "a@test.com", "12345")

        insert_call = next(
            c for c in self.cursor.execute.call_args_list if "INSERT INTO users" in c.args[0]
        )
        params = insert_call.args[1]
        self.assertIn("hashed-value", params)
        self.assertNotIn("plaintext-pw", params)


if __name__ == "__main__":
    unittest.main()
