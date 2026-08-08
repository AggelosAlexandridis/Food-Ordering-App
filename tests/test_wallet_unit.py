import unittest
from unittest.mock import MagicMock

from db.wallet import Wallet


class TestWalletUnit(unittest.TestCase):
    """Pure unit tests: the DB connection/cursor are mocked, no real DB is touched."""

    def setUp(self):
        self.conn = MagicMock()
        self.cursor = self.conn.cursor.return_value.__enter__.return_value
        self.wallet = Wallet(self.conn)

    def test_get_balance_returns_float(self):
        self.cursor.fetchone.return_value = (42.5,)

        result = self.wallet.get_balance(1)

        self.assertEqual(result, 42.5)
        self.assertIsInstance(result, float)

    def test_get_balance_returns_none_when_wallet_missing(self):
        self.cursor.fetchone.return_value = None

        result = self.wallet.get_balance(999)

        self.assertIsNone(result)

    def test_get_balance_query_filters_by_user_id(self):
        self.cursor.fetchone.return_value = (10.0,)

        self.wallet.get_balance(3)

        query, params = self.cursor.execute.call_args.args
        self.assertIn("WHERE user_id=%s", query)
        self.assertEqual(params, (3,))

    def test_update_balance_commits_and_returns_true_on_success(self):
        result = self.wallet.update_balance(1, 100.0)

        self.assertTrue(result)
        self.conn.commit.assert_called_once()
        self.conn.rollback.assert_not_called()

    def test_update_balance_uses_correct_params(self):
        self.wallet.update_balance(5, 12.34)

        query, params = self.cursor.execute.call_args.args
        self.assertIn("UPDATE wallets SET balance=%s WHERE user_id=%s", query)
        self.assertEqual(params, (12.34, 5))

    def test_update_balance_rolls_back_and_returns_false_on_db_error(self):
        self.cursor.execute.side_effect = Exception("connection lost")

        result = self.wallet.update_balance(1, 100.0)

        self.assertFalse(result)
        self.conn.rollback.assert_called_once()
        self.conn.commit.assert_not_called()


if __name__ == "__main__":
    unittest.main()
