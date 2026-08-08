import unittest
from datetime import date
from unittest.mock import MagicMock

from db.cards import Cards


class TestCardsUnit(unittest.TestCase):
    """Pure unit tests: the DB connection/cursor are mocked, no real DB is touched."""

    def setUp(self):
        self.conn = MagicMock()
        self.cursor = self.conn.cursor.return_value.__enter__.return_value
        self.cards = Cards(self.conn)

    def test_get_cards_formats_masked_display_text(self):
        self.cursor.fetchall.return_value = [
            (1, "1234567812345678", "Alice Doe", date(2027, 5, 1), "VISA"),
        ]

        result = self.cards.get_cards(1)

        self.assertEqual(len(result), 1)
        card = result[0]
        self.assertEqual(card["card_number"], "1234567812345678")
        self.assertEqual(card["text"], "Visa •••• 5678  ·  exp 05/27")

    def test_get_cards_empty(self):
        self.cursor.fetchall.return_value = []

        self.assertEqual(self.cards.get_cards(1), [])

    def test_add_card_commits_and_returns_true(self):
        result = self.cards.add_card(
            user_id=1,
            card_number="1111222233334444",
            cvv=123,
            card_holder_name="Alice Doe",
            expiration_date=date(2028, 1, 1),
            card_type="VISA",
        )

        self.assertTrue(result)
        self.conn.commit.assert_called_once()

    def test_add_card_rolls_back_on_db_error(self):
        self.cursor.execute.side_effect = Exception("duplicate card")

        result = self.cards.add_card(1, "1111222233334444", 123, "Alice", date(2028, 1, 1), "VISA")

        self.assertFalse(result)
        self.conn.rollback.assert_called_once()

    def test_delete_card_scopes_by_owner_and_id(self):
        result = self.cards.delete_card(user_id=1, card_id=5)

        self.assertTrue(result)
        query, params = self.cursor.execute.call_args.args
        self.assertIn("WHERE id = %s AND user_id = %s", query)
        self.assertEqual(params, (5, 1))

    def test_delete_card_rolls_back_on_db_error(self):
        self.cursor.execute.side_effect = Exception("db error")

        result = self.cards.delete_card(1, 5)

        self.assertFalse(result)
        self.conn.rollback.assert_called_once()


if __name__ == "__main__":
    unittest.main()
