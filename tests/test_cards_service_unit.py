import unittest
from datetime import date, timedelta
from unittest.mock import MagicMock

from services.cards import Cards


class TestListCardsUnit(unittest.TestCase):
    def setUp(self):
        self.db = MagicMock()
        self.service = Cards(self.db)

    def test_formats_masked_display_text(self):
        self.db.cards.get_cards.return_value = [
            (1, "1234567812345678", "Alice Doe", date(2027, 5, 1), "VISA"),
        ]

        result = self.service.list_cards(1)

        self.assertEqual(len(result), 1)
        card = result[0]
        self.assertEqual(card["card_number"], "1234567812345678")
        self.assertEqual(card["text"], "Visa •••• 5678  ·  exp 05/27")

    def test_empty(self):
        self.db.cards.get_cards.return_value = []

        self.assertEqual(self.service.list_cards(1), [])


class TestAddCardUnit(unittest.TestCase):
    def setUp(self):
        self.db = MagicMock()
        self.service = Cards(self.db)

    def _future_expiry(self):
        future = date.today() + timedelta(days=400)
        return future.strftime("%m/%y")

    def test_rejects_missing_holder(self):
        success, error = self.service.add_card(1, "  ", "1111222233334444", "123", self._future_expiry(), "VISA")

        self.assertFalse(success)
        self.assertIn("name on the card", error)
        self.db.cards.add_card.assert_not_called()

    def test_rejects_non_16_digit_card_number(self):
        success, error = self.service.add_card(1, "Alice", "123", "123", self._future_expiry(), "VISA")

        self.assertFalse(success)
        self.assertIn("16 digits", error)

    def test_rejects_invalid_cvv(self):
        success, error = self.service.add_card(1, "Alice", "1111222233334444", "12", self._future_expiry(), "VISA")

        self.assertFalse(success)
        self.assertIn("CVV", error)

    def test_rejects_malformed_expiry(self):
        success, error = self.service.add_card(1, "Alice", "1111222233334444", "123", "13/99", "VISA")

        self.assertFalse(success)
        self.assertIn("MM/YY", error)

    def test_rejects_expired_card(self):
        success, error = self.service.add_card(1, "Alice", "1111222233334444", "123", "01/20", "VISA")

        self.assertFalse(success)
        self.assertIn("expired", error)

    def test_valid_card_is_saved(self):
        self.db.cards.add_card.return_value = True

        success, error = self.service.add_card(
            1, " Alice Doe ", " 1111222233334444 ", " 123 ", self._future_expiry(), "VISA"
        )

        self.assertTrue(success)
        self.assertIsNone(error)
        self.db.cards.add_card.assert_called_once()
        args = self.db.cards.add_card.call_args.args
        self.assertEqual(args[0], 1)
        self.assertEqual(args[1], "1111222233334444")
        self.assertEqual(args[3], "Alice Doe")

    def test_db_failure_returns_friendly_error(self):
        self.db.cards.add_card.return_value = False

        success, error = self.service.add_card(1, "Alice", "1111222233334444", "123", self._future_expiry(), "VISA")

        self.assertFalse(success)
        self.assertIn("Error saving card", error)


class TestDeleteCardUnit(unittest.TestCase):
    def test_delegates_to_repository(self):
        db = MagicMock()
        db.cards.delete_card.return_value = True
        service = Cards(db)

        self.assertTrue(service.delete_card(1, 5))
        db.cards.delete_card.assert_called_once_with(1, 5)


if __name__ == "__main__":
    unittest.main()
