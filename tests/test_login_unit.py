import unittest
from unittest.mock import MagicMock

from db.login import Login


class TestLoginUnit(unittest.TestCase):
    """Pure unit tests: the DB connection/cursor are mocked, no real DB is touched."""

    def setUp(self):
        self.conn = MagicMock()
        self.cursor = self.conn.cursor.return_value.__enter__.return_value
        self.login = Login(self.conn)

    def test_valid_credentials_returns_id_and_role(self):
        self.cursor.fetchone.return_value = (1, "CUSTOMER")

        result = self.login.check_login("alice", "secret")

        self.assertEqual(result, [1, "CUSTOMER"])

    def test_invalid_credentials_returns_none(self):
        self.cursor.fetchone.return_value = None

        result = self.login.check_login("alice", "wrongpass")

        self.assertIsNone(result)

    def test_login_query_checks_username_or_email(self):
        self.cursor.fetchone.return_value = None

        self.login.check_login("alice@test.com", "secret")

        query, params = self.cursor.execute.call_args.args
        self.assertIn("username=%s OR email=%s", query)
        self.assertEqual(params, ("alice@test.com", "alice@test.com", "secret"))

    def test_login_uses_a_single_cursor_context(self):
        self.cursor.fetchone.return_value = (7, "CHEF")

        self.login.check_login("bob", "pw")

        self.conn.cursor.assert_called_once()
        self.cursor.execute.assert_called_once()


if __name__ == "__main__":
    unittest.main()
