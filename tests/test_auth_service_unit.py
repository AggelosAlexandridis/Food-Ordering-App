import unittest
from unittest.mock import MagicMock, patch

from services.auth import Auth


class TestLoginUnit(unittest.TestCase):
    def setUp(self):
        self.db = MagicMock()
        self.service = Auth(self.db)

    def test_unknown_username_returns_none(self):
        self.db.login.find_credentials.return_value = None

        self.assertIsNone(self.service.login("alice", "wrongpass"))

    @patch("services.auth.verify_password", return_value=True)
    def test_valid_credentials_returns_id_and_role(self, _mock_verify):
        self.db.login.find_credentials.return_value = (1, "CUSTOMER", "some-stored-hash")

        result = self.service.login("alice", "secret")

        self.assertEqual(result, [1, "CUSTOMER"])

    @patch("services.auth.verify_password", return_value=False)
    def test_wrong_password_returns_none(self, _mock_verify):
        self.db.login.find_credentials.return_value = (1, "CUSTOMER", "some-stored-hash")

        self.assertIsNone(self.service.login("alice", "wrongpass"))

    @patch("services.auth.verify_password", return_value=True)
    def test_verify_password_called_with_plaintext_and_stored_hash(self, mock_verify):
        self.db.login.find_credentials.return_value = (7, "CHEF", "the-stored-hash")

        self.service.login("bob", "pw")

        mock_verify.assert_called_once_with("pw", "the-stored-hash")


class TestRegisterValidationUnit(unittest.TestCase):
    def setUp(self):
        self.db = MagicMock()
        self.db.login.username_exists.return_value = False
        self.db.login.email_exists.return_value = False
        self.db.login.phone_exists.return_value = False
        self.service = Auth(self.db)

    def test_rejects_missing_fields(self):
        user_id, error = self.service.register("", "secret1", "secret1", "a@test.com", "12345")

        self.assertIsNone(user_id)
        self.assertIn("fill in all fields", error)
        self.db.login.create_user.assert_not_called()

    def test_rejects_invalid_email(self):
        user_id, error = self.service.register("alice", "secret1", "secret1", "not-an-email", "12345")

        self.assertIsNone(user_id)
        self.assertIn("valid email", error)

    def test_rejects_short_password(self):
        user_id, error = self.service.register("alice", "abc", "abc", "a@test.com", "12345")

        self.assertIsNone(user_id)
        self.assertIn("6 characters", error)

    def test_rejects_mismatched_confirmation(self):
        user_id, error = self.service.register("alice", "secret1", "secret2", "a@test.com", "12345")

        self.assertIsNone(user_id)
        self.assertIn("do not match", error)

    def test_rejects_duplicate_username(self):
        self.db.login.username_exists.return_value = True

        user_id, error = self.service.register("alice", "secret1", "secret1", "a@test.com", "12345")

        self.assertIsNone(user_id)
        self.assertIn("username", error)

    def test_rejects_duplicate_email(self):
        self.db.login.email_exists.return_value = True

        user_id, error = self.service.register("alice", "secret1", "secret1", "a@test.com", "12345")

        self.assertIsNone(user_id)
        self.assertIn("email", error)

    def test_rejects_duplicate_phone(self):
        self.db.login.phone_exists.return_value = True

        user_id, error = self.service.register("alice", "secret1", "secret1", "a@test.com", "12345")

        self.assertIsNone(user_id)
        self.assertIn("phone number", error)

    @patch("services.auth.hash_password", return_value="hashed-value")
    def test_valid_registration_hashes_password_and_creates_user(self, _mock_hash):
        self.db.login.create_user.return_value = 42

        user_id, error = self.service.register("alice", "secret1", "secret1", "a@test.com", "12345")

        self.assertEqual(user_id, 42)
        self.assertIsNone(error)
        self.db.login.create_user.assert_called_once_with("alice", "hashed-value", "a@test.com", "12345")

    def test_db_failure_returns_friendly_error(self):
        self.db.login.create_user.return_value = None

        user_id, error = self.service.register("alice", "secret1", "secret1", "a@test.com", "12345")

        self.assertIsNone(user_id)
        self.assertIn("Error creating account", error)


if __name__ == "__main__":
    unittest.main()
