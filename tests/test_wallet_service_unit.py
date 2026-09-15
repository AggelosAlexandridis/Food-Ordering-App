import unittest
from unittest.mock import MagicMock

from services.wallet import Wallet


class TestGetBalanceUnit(unittest.TestCase):
    def test_delegates_to_repository(self):
        db = MagicMock()
        db.wallet.get_balance.return_value = 42.5
        service = Wallet(db)

        self.assertEqual(service.get_balance(1), 42.5)


class TestAddFundsUnit(unittest.TestCase):
    def setUp(self):
        self.db = MagicMock()
        self.service = Wallet(self.db)

    def test_rejects_non_numeric_amount(self):
        success, amount, new_balance, error = self.service.add_funds(1, "abc")

        self.assertFalse(success)
        self.assertIsNone(amount)
        self.assertIsNone(new_balance)
        self.assertIn("valid positive amount", error)
        self.db.wallet.update_balance.assert_not_called()

    def test_rejects_zero_or_negative_amount(self):
        success, amount, new_balance, error = self.service.add_funds(1, "0")

        self.assertFalse(success)
        self.assertIn("valid positive amount", error)

    def test_adds_amount_to_current_balance(self):
        self.db.wallet.get_balance.return_value = 10.0

        success, amount, new_balance, error = self.service.add_funds(1, "25.5")

        self.assertTrue(success)
        self.assertEqual(amount, 25.5)
        self.assertEqual(new_balance, 35.5)
        self.assertIsNone(error)
        self.db.wallet.update_balance.assert_called_once_with(1, 35.5)


if __name__ == "__main__":
    unittest.main()
