import unittest

from db.passwords import hash_password, is_hashed, verify_password


class TestHashPassword(unittest.TestCase):
    def test_hash_has_expected_format(self):
        hashed = hash_password("secret123")
        parts = hashed.split("$")

        self.assertEqual(len(parts), 4)
        self.assertEqual(parts[0], "pbkdf2_sha256")

    def test_same_password_hashed_twice_produces_different_salts(self):
        first = hash_password("secret123")
        second = hash_password("secret123")

        self.assertNotEqual(first, second)


class TestVerifyPassword(unittest.TestCase):
    def test_correct_password_verifies(self):
        hashed = hash_password("secret123")
        self.assertTrue(verify_password("secret123", hashed))

    def test_wrong_password_fails(self):
        hashed = hash_password("secret123")
        self.assertFalse(verify_password("wrong-password", hashed))

    def test_legacy_plaintext_password_still_verifies(self):
        # rows created before the hashing migration store the raw password
        self.assertTrue(verify_password("1234", "1234"))

    def test_legacy_plaintext_wrong_password_fails(self):
        self.assertFalse(verify_password("wrong", "1234"))

    def test_empty_stored_password_does_not_crash(self):
        self.assertFalse(verify_password("anything", ""))
        self.assertFalse(verify_password("anything", None))


class TestIsHashed(unittest.TestCase):
    def test_hashed_value_is_detected(self):
        self.assertTrue(is_hashed(hash_password("secret123")))

    def test_plaintext_value_is_not_detected_as_hashed(self):
        self.assertFalse(is_hashed("1234"))
        self.assertFalse(is_hashed(""))
        self.assertFalse(is_hashed(None))


if __name__ == "__main__":
    unittest.main()
