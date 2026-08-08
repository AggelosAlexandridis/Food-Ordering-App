import unittest
from datetime import datetime
from unittest.mock import MagicMock

from db.orders import Orders


class TestGetCartItemsUnit(unittest.TestCase):
    """Pure unit tests: the DB connection/cursor are mocked, no real DB is touched."""

    def setUp(self):
        self.conn = MagicMock()
        self.cursor = self.conn.cursor.return_value.__enter__.return_value
        self.orders = Orders(self.conn)

    def test_empty_cart_short_circuits_without_touching_db(self):
        result = self.orders.get_cart_items([])

        self.assertEqual(result, [])
        self.conn.cursor.assert_not_called()

    def test_aggregates_duplicate_line_items_by_quantity(self):
        self.cursor.fetchall.return_value = [(1, "Burger", 10.0)]

        cart = [{"id": 1, "quantity": 2}, {"id": 1, "quantity": 1}]
        result = self.orders.get_cart_items(cart)

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["price"], 30.0)
        self.assertIn("x3", result[0]["text"])

    def test_builds_in_clause_with_one_placeholder_per_id(self):
        self.cursor.fetchall.return_value = []

        self.orders.get_cart_items([{"id": 1, "quantity": 1}, {"id": 2, "quantity": 1}])

        query, params = self.cursor.execute.call_args.args
        self.assertIn("IN (%s,%s)", query)
        self.assertEqual(params, [1, 2])

    def test_food_ids_not_returned_by_db_are_silently_dropped(self):
        # only id 1 is a "real" row even though the cart references id 2 as well
        self.cursor.fetchall.return_value = [(1, "Burger", 10.0)]

        result = self.orders.get_cart_items([{"id": 1, "quantity": 1}, {"id": 2, "quantity": 1}])

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["id"], 1)


class TestSubmitOrderUnit(unittest.TestCase):
    def setUp(self):
        self.conn = MagicMock()
        self.cursor = self.conn.cursor.return_value.__enter__.return_value
        self.orders = Orders(self.conn)

    def test_card_payment_with_wallet_commits_and_returns_true(self):
        self.cursor.fetchone.return_value = (55,)  # wallet_id lookup

        result = self.orders.submit_order(1, 2, 25.5, "CARD")

        self.assertTrue(result)
        self.conn.commit.assert_called_once()

    def test_card_payment_without_wallet_returns_false_without_committing(self):
        self.cursor.fetchone.return_value = None  # no wallet row for this user

        result = self.orders.submit_order(1, 2, 25.5, "CARD")

        self.assertFalse(result)
        self.conn.commit.assert_not_called()

    def test_card_insert_uses_looked_up_wallet_id(self):
        self.cursor.fetchone.return_value = (99,)

        self.orders.submit_order(1, 2, 25.5, "CARD", notes="ring the bell")

        insert_query, insert_params = self.cursor.execute.call_args.args
        self.assertIn("INSERT INTO orders", insert_query)
        self.assertEqual(insert_params, (1, None, 2, 25.5, 0, "ring the bell", "CARD", 99))

    def test_insert_passes_through_restaurant_id_and_tip(self):
        self.cursor.fetchone.return_value = (99,)

        self.orders.submit_order(1, 2, 25.5, "CARD", restaurant_id=7, tip=3.5)

        _, insert_params = self.cursor.execute.call_args.args
        self.assertEqual(insert_params, (1, 7, 2, 25.5, 3.5, None, "CARD", 99))

    def test_cash_payment_skips_wallet_lookup(self):
        result = self.orders.submit_order(1, 2, 25.5, "CASH")

        self.assertTrue(result)
        # only the INSERT should run - no SELECT against wallets
        self.assertEqual(self.cursor.execute.call_count, 1)
        insert_query, insert_params = self.cursor.execute.call_args.args
        self.assertIsNone(insert_params[-1])  # wallet_id stays None for CASH

    def test_db_error_during_insert_rolls_back_and_returns_false(self):
        self.cursor.execute.side_effect = Exception("db is down")

        result = self.orders.submit_order(1, 2, 25.5, "CASH")

        self.assertFalse(result)
        self.conn.rollback.assert_called_once()
        self.conn.commit.assert_not_called()


class TestGetUserOrdersUnit(unittest.TestCase):
    def setUp(self):
        self.conn = MagicMock()
        self.cursor = self.conn.cursor.return_value.__enter__.return_value
        self.orders = Orders(self.conn)

    def test_no_orders_returns_empty_list(self):
        self.cursor.fetchall.return_value = []

        result = self.orders.get_user_orders(1)

        self.assertEqual(result, [])

    def test_formats_order_summary_text(self):
        self.cursor.fetchall.return_value = [
            (7, 42.0, 0, "PENDING", datetime(2026, 1, 2, 13, 30)),
        ]

        result = self.orders.get_user_orders(1)

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
        self.cursor.fetchall.return_value = [
            (7, 42.0, 5.0, "PENDING", datetime(2026, 1, 2, 13, 30)),
        ]

        result = self.orders.get_user_orders(1)

        text = result[0]["text"]
        self.assertIn("Total: 47.00€", text)
        self.assertIn("incl. 5.00€ tip", text)


class TestCancelOrderByCustomerUnit(unittest.TestCase):
    def setUp(self):
        self.conn = MagicMock()
        self.cursor = self.conn.cursor.return_value.__enter__.return_value
        self.orders = Orders(self.conn)

    def test_cancels_pending_order_owned_by_user(self):
        self.cursor.rowcount = 1

        result = self.orders.cancel_order_by_customer(5, 9)

        self.assertTrue(result)
        self.conn.commit.assert_called_once()
        query, params = self.cursor.execute.call_args.args
        self.assertIn("status = 'PENDING'", query)
        self.assertEqual(params, (5, 9))

    def test_fails_when_not_owner_or_not_pending(self):
        self.cursor.rowcount = 0

        result = self.orders.cancel_order_by_customer(5, 9)

        self.assertFalse(result)
        self.conn.rollback.assert_called_once()
        self.conn.commit.assert_not_called()


class TestGetRestaurantOrdersUnit(unittest.TestCase):
    def setUp(self):
        self.conn = MagicMock()
        self.cursor = self.conn.cursor.return_value.__enter__.return_value
        self.orders = Orders(self.conn)

    def test_formats_status_and_optional_tip_and_note(self):
        self.cursor.fetchall.return_value = [
            (7, 20.0, 3.0, "PENDING", datetime(2026, 1, 2, 13, 30), "no onions"),
            (8, 15.0, 0.0, "READY", datetime(2026, 1, 2, 14, 0), None),
        ]

        result = self.orders.get_restaurant_orders(1)

        self.assertEqual(len(result), 2)
        self.assertIn("+ 3.00€ tip", result[0]["text"])
        self.assertIn("Note: no onions", result[0]["text"])
        self.assertNotIn("tip", result[1]["text"])
        self.assertNotIn("Note:", result[1]["text"])
        self.assertEqual(result[0]["status"], "PENDING")

    def test_long_note_is_truncated(self):
        long_note = "x" * 80
        self.cursor.fetchall.return_value = [
            (1, 10.0, 0.0, "PENDING", datetime(2026, 1, 1, 0, 0), long_note),
        ]

        result = self.orders.get_restaurant_orders(1)

        self.assertIn("...", result[0]["text"])
        self.assertNotIn(long_note, result[0]["text"])


class TestChefTransitionsUnit(unittest.TestCase):
    def setUp(self):
        self.conn = MagicMock()
        self.cursor = self.conn.cursor.return_value.__enter__.return_value
        self.orders = Orders(self.conn)

    def test_confirm_order_commits_when_row_matched(self):
        self.cursor.rowcount = 1

        result = self.orders.confirm_order(1, 2, 3)

        self.assertTrue(result)
        self.conn.commit.assert_called_once()
        query, params = self.cursor.execute.call_args.args
        self.assertIn("CONFIRMED", query)
        self.assertEqual(params, (3, 1, 2))

    def test_confirm_order_rolls_back_when_no_row_matched(self):
        self.cursor.rowcount = 0

        result = self.orders.confirm_order(1, 2, 3)

        self.assertFalse(result)
        self.conn.rollback.assert_called_once()
        self.conn.commit.assert_not_called()

    def test_mark_order_ready_scoped_to_restaurant_and_chef(self):
        self.cursor.rowcount = 1

        self.orders.mark_order_ready(1, 2, 3)

        query, params = self.cursor.execute.call_args.args
        self.assertIn("READY", query)
        self.assertEqual(params, (1, 2, 3))

    def test_cancel_order_by_chef_allows_pending_or_confirmed(self):
        self.cursor.rowcount = 1

        result = self.orders.cancel_order_by_chef(1, 2, 3)

        self.assertTrue(result)
        query, params = self.cursor.execute.call_args.args
        self.assertIn("CANCELLED", query)
        self.assertEqual(params, (3, 1, 2))

    def test_db_error_rolls_back_and_returns_false(self):
        self.cursor.execute.side_effect = Exception("boom")

        result = self.orders.confirm_order(1, 2, 3)

        self.assertFalse(result)
        self.conn.rollback.assert_called_once()


class TestDeliveryQueriesUnit(unittest.TestCase):
    def setUp(self):
        self.conn = MagicMock()
        self.cursor = self.conn.cursor.return_value.__enter__.return_value
        self.orders = Orders(self.conn)

    def test_get_ready_orders_empty_restaurant_list_short_circuits(self):
        result = self.orders.get_ready_orders_for_restaurants([])

        self.assertEqual(result, [])
        self.conn.cursor.assert_not_called()

    def test_get_ready_orders_formats_text_with_restaurant_name(self):
        self.cursor.fetchall.return_value = [(5, 12.5, 1, "Pizzaria", datetime(2026, 1, 1))]

        result = self.orders.get_ready_orders_for_restaurants([1, 2])

        self.assertEqual(result[0]["restaurant_id"], 1)
        self.assertIn("Pizzaria", result[0]["text"])
        query, params = self.cursor.execute.call_args.args
        self.assertIn("IN (%s,%s)", query)
        self.assertEqual(params, [1, 2])

    def test_claim_order_succeeds_when_row_matched(self):
        self.cursor.rowcount = 1

        result = self.orders.claim_order_for_delivery(5, 9)

        self.assertTrue(result)
        self.conn.commit.assert_called_once()

    def test_claim_order_fails_when_already_claimed(self):
        # simulates the race: another delivery person's UPDATE already moved
        # the row out of READY/NULL, so this UPDATE matches zero rows
        self.cursor.rowcount = 0

        result = self.orders.claim_order_for_delivery(5, 9)

        self.assertFalse(result)
        self.conn.rollback.assert_called_once()
        self.conn.commit.assert_not_called()

    def test_mark_order_delivered_scoped_to_delivery_user(self):
        self.cursor.rowcount = 1

        self.orders.mark_order_delivered(5, 9)

        query, params = self.cursor.execute.call_args.args
        self.assertIn("UPDATE orders", query)
        self.assertEqual(params, ("DELIVERED", 5, 9))

    def test_cancel_order_by_delivery_fails_if_not_owner(self):
        self.cursor.rowcount = 0

        result = self.orders.cancel_order_by_delivery(5, 999)

        self.assertFalse(result)


class TestDeliveryIncomeUnit(unittest.TestCase):
    def setUp(self):
        self.conn = MagicMock()
        self.cursor = self.conn.cursor.return_value.__enter__.return_value
        self.orders = Orders(self.conn)

    def test_no_deliveries_returns_zeroed_income(self):
        self.cursor.fetchone.return_value = (0, 0)

        result = self.orders.get_delivery_income(9)

        self.assertEqual(result, {"deliveries": 0, "flat_fees": 0.0, "tips": 0.0, "total": 0.0})

    def test_combines_flat_fee_per_delivery_with_summed_tips(self):
        self.cursor.fetchone.return_value = (2, 5.0)

        result = self.orders.get_delivery_income(9)

        self.assertEqual(result["deliveries"], 2)
        self.assertEqual(result["flat_fees"], 2 * Orders.DELIVERY_FLAT_FEE)
        self.assertEqual(result["tips"], 5.0)
        self.assertEqual(result["total"], 2 * Orders.DELIVERY_FLAT_FEE + 5.0)


if __name__ == "__main__":
    unittest.main()
