import unittest
from datetime import datetime
from unittest.mock import MagicMock

from services.orders import DELIVERY_FLAT_FEE, Orders


class TestGetCartItemsUnit(unittest.TestCase):
    def setUp(self):
        self.db = MagicMock()
        self.service = Orders(self.db)

    def test_empty_cart_short_circuits_without_touching_db(self):
        result = self.service.get_cart_items([])

        self.assertEqual(result, [])
        self.db.orders.get_food_prices.assert_not_called()

    def test_aggregates_duplicate_line_items_by_quantity(self):
        self.db.orders.get_food_prices.return_value = [(1, "Burger", 10.0)]

        cart = [{"id": 1, "quantity": 2}, {"id": 1, "quantity": 1}]
        result = self.service.get_cart_items(cart)

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["price"], 30.0)
        self.assertIn("x3", result[0]["text"])

    def test_food_ids_not_returned_by_db_are_silently_dropped(self):
        self.db.orders.get_food_prices.return_value = [(1, "Burger", 10.0)]

        result = self.service.get_cart_items([{"id": 1, "quantity": 1}, {"id": 2, "quantity": 1}])

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["id"], 1)


class TestCheckoutUnit(unittest.TestCase):
    def setUp(self):
        self.db = MagicMock()
        self.service = Orders(self.db)

    def test_cash_order_skips_wallet_entirely(self):
        self.db.orders.insert_order.return_value = True

        success, error = self.service.checkout(1, 7, 2, "CASH", 25.5, 0, None)

        self.assertTrue(success)
        self.assertIsNone(error)
        self.db.wallet.get_balance.assert_not_called()
        self.db.orders.insert_order.assert_called_once_with(
            1, 2, 25.5, "CASH", None, restaurant_id=7, tip=0,
        )

    def test_cash_order_db_failure_returns_error(self):
        self.db.orders.insert_order.return_value = False

        success, error = self.service.checkout(1, 7, 2, "CASH", 25.5, 0, None)

        self.assertFalse(success)
        self.assertIn("Checkout Error", error)

    def test_card_order_without_wallet_fails(self):
        self.db.wallet.get_balance.return_value = None

        success, error = self.service.checkout(1, 7, 2, "CARD", 25.5, 0, None)

        self.assertFalse(success)
        self.assertIn("Wallet not found", error)
        self.db.orders.insert_order.assert_not_called()

    def test_card_order_insufficient_funds_fails(self):
        self.db.wallet.get_balance.return_value = 10.0

        success, error = self.service.checkout(1, 7, 2, "CARD", 25.5, 0, None)

        self.assertFalse(success)
        self.assertIn("Insufficient funds", error)
        self.db.orders.insert_order.assert_not_called()

    def test_card_order_success_inserts_and_deducts_balance(self):
        self.db.wallet.get_balance.return_value = 100.0
        self.db.wallet.get_wallet_id.return_value = 99
        self.db.orders.insert_order.return_value = True

        success, error = self.service.checkout(1, 7, 2, "CARD", 25.0, 5.0, "ring the bell")

        self.assertTrue(success)
        self.assertIsNone(error)
        self.db.orders.insert_order.assert_called_once_with(
            1, 2, 25.0, "CARD", "ring the bell", restaurant_id=7, tip=5.0, wallet_id=99,
        )
        self.db.wallet.update_balance.assert_called_once_with(1, 70.0)

    def test_card_order_db_failure_does_not_deduct_balance(self):
        self.db.wallet.get_balance.return_value = 100.0
        self.db.wallet.get_wallet_id.return_value = 99
        self.db.orders.insert_order.return_value = False

        success, error = self.service.checkout(1, 7, 2, "CARD", 25.0, 0, None)

        self.assertFalse(success)
        self.db.wallet.update_balance.assert_not_called()


class TestListUserOrdersUnit(unittest.TestCase):
    def test_formats_order_summary_text(self):
        db = MagicMock()
        db.orders.get_user_orders.return_value = [
            (7, 42.0, 0, "PENDING", datetime(2026, 1, 2, 13, 30)),
        ]
        service = Orders(db)

        result = service.list_user_orders(1)

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["id"], 7)
        self.assertEqual(result[0]["status"], "PENDING")
        text = result[0]["text"]
        self.assertIn("Order #7", text)
        self.assertIn("Status: PENDING", text)
        self.assertIn("Total: 42.00€", text)
        self.assertIn("2026-01-02 13:30", text)
        self.assertNotIn("tip", text)

    def test_total_includes_tip_and_notes_it_separately(self):
        db = MagicMock()
        db.orders.get_user_orders.return_value = [
            (7, 42.0, 5.0, "PENDING", datetime(2026, 1, 2, 13, 30)),
        ]
        service = Orders(db)

        text = service.list_user_orders(1)[0]["text"]

        self.assertIn("Total: 47.00€", text)
        self.assertIn("incl. 5.00€ tip", text)


class TestListRestaurantOrdersUnit(unittest.TestCase):
    def test_formats_status_and_optional_tip_and_note(self):
        db = MagicMock()
        db.orders.get_restaurant_orders.return_value = [
            (7, 20.0, 3.0, "PENDING", datetime(2026, 1, 2, 13, 30), "no onions"),
            (8, 15.0, 0.0, "READY", datetime(2026, 1, 2, 14, 0), None),
        ]
        service = Orders(db)

        result = service.list_restaurant_orders(1)

        self.assertEqual(len(result), 2)
        self.assertIn("+ 3.00€ tip", result[0]["text"])
        self.assertIn("Note: no onions", result[0]["text"])
        self.assertNotIn("tip", result[1]["text"])
        self.assertNotIn("Note:", result[1]["text"])
        self.assertEqual(result[0]["status"], "PENDING")

    def test_long_note_is_truncated(self):
        long_note = "x" * 80
        db = MagicMock()
        db.orders.get_restaurant_orders.return_value = [
            (1, 10.0, 0.0, "PENDING", datetime(2026, 1, 1, 0, 0), long_note),
        ]
        service = Orders(db)

        text = service.list_restaurant_orders(1)[0]["text"]

        self.assertIn("...", text)
        self.assertNotIn(long_note, text)


class TestChefTransitionsUnit(unittest.TestCase):
    def test_confirm_order_delegates_to_repository(self):
        db = MagicMock()
        db.orders.confirm_order.return_value = True
        service = Orders(db)

        self.assertTrue(service.confirm_order(1, 2, 3))
        db.orders.confirm_order.assert_called_once_with(1, 2, 3)


class TestListReadyOrdersUnit(unittest.TestCase):
    def test_formats_text_with_restaurant_name(self):
        db = MagicMock()
        db.orders.get_ready_orders_for_restaurants.return_value = [
            (5, 12.5, 1, "Pizzaria", datetime(2026, 1, 1)),
        ]
        service = Orders(db)

        result = service.list_ready_orders([1, 2])

        self.assertEqual(result[0]["restaurant_id"], 1)
        self.assertIn("Pizzaria", result[0]["text"])


class TestDeliveryIncomeUnit(unittest.TestCase):
    def test_no_deliveries_returns_zeroed_income(self):
        db = MagicMock()
        db.orders.get_delivery_income_raw.return_value = (0, 0.0)
        service = Orders(db)

        result = service.get_delivery_income(9)

        self.assertEqual(result, {"deliveries": 0, "flat_fees": 0.0, "tips": 0.0, "total": 0.0})

    def test_combines_flat_fee_per_delivery_with_summed_tips(self):
        db = MagicMock()
        db.orders.get_delivery_income_raw.return_value = (2, 5.0)
        service = Orders(db)

        result = service.get_delivery_income(9)

        self.assertEqual(result["deliveries"], 2)
        self.assertEqual(result["flat_fees"], 2 * DELIVERY_FLAT_FEE)
        self.assertEqual(result["tips"], 5.0)
        self.assertEqual(result["total"], 2 * DELIVERY_FLAT_FEE + 5.0)


if __name__ == "__main__":
    unittest.main()
