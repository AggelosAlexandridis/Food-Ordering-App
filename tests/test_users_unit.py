import unittest
from unittest.mock import MagicMock

from db.users import Users


class TestUsersUnit(unittest.TestCase):
    """Pure unit tests: the DB connection/cursor are mocked, no real DB is touched."""

    def setUp(self):
        self.conn = MagicMock()
        self.cursor = self.conn.cursor.return_value.__enter__.return_value
        self.users = Users(self.conn)

    def test_get_profile_returns_dict(self):
        self.cursor.fetchone.return_value = ("alice", "Alice Doe", "alice@test.com", "1234567890")

        result = self.users.get_profile(1)

        self.assertEqual(result, {
            "username": "alice",
            "name": "Alice Doe",
            "email": "alice@test.com",
            "phone_number": "1234567890",
        })

    def test_get_profile_returns_none_when_missing(self):
        self.cursor.fetchone.return_value = None

        self.assertIsNone(self.users.get_profile(999999))

    def test_update_name_commits_and_returns_true(self):
        result = self.users.update_name(1, "New Name")

        self.assertTrue(result)
        self.conn.commit.assert_called_once()
        query, params = self.cursor.execute.call_args.args
        self.assertIn("UPDATE users SET name = %s WHERE id = %s", query)
        self.assertEqual(params, ("New Name", 1))

    def test_update_name_rolls_back_on_db_error(self):
        self.cursor.execute.side_effect = Exception("db error")

        result = self.users.update_name(1, "New Name")

        self.assertFalse(result)
        self.conn.rollback.assert_called_once()


if __name__ == "__main__":
    unittest.main()
