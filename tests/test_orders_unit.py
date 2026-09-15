import unittest
from datetime import datetime
from unittest.mock import MagicMock

from db.orders import Orders


class TestGetFoodPricesUnit(unittest.TestCase):
    def setUp(self):
        self.conn = MagicMock()
        self.cursor = self.conn.cursor.return_value.__enter__.return_value
        self.orders = Orders(self.conn)

    def test_empty_ids_short_circuits_without_touching_db(self):
        result = self.orders.get_food_prices([])

        self.assertEqual(result, [])
        self.conn.cursor.assert_not_called()

    def test_builds_in_clause_with_one_placeholder_per_id(self):
        self.cursor.fetchall.return_value = []

        self.orders.get_food_prices([1, 2])

        query, params = self.cursor.execute.call_args.args
        self.assertIn("IN (%s,%s)", query)
        self.assertEqual(params, [1, 2])

    def test_returns_raw_rows(self):
        self.cursor.fetchall.return_value = [(1, "Burger", 10.0)]

        result = self.orders.get_food_prices([1])

        self.assertEqual(result, [(1, "Burger", 10.0)])


class TestInsertOrderUnit(unittest.TestCase):
    def setUp(self):
        self.conn = MagicMock()
        self.cursor = self.conn.cursor.return_value.__enter__.return_value
        self.orders = Orders(self.conn)

    def test_commits_and_returns_true(self):
        result = self.orders.insert_order(1, 2, 25.5, "CARD", wallet_id=99)

        self.assertTrue(result)
        self.conn.commit.assert_called_once()

    def test_insert_uses_given_wallet_id(self):
        self.orders.insert_order(1, 2, 25.5, "CARD", notes="ring the bell", wallet_id=99)

        insert_query, insert_params = self.cursor.execute.call_args.args
        self.assertIn("INSERT INTO orders", insert_query)
        self.assertEqual(insert_params, (1, None, 2, 25.5, 0, "ring the bell", "CARD", 99))

    def test_passes_through_restaurant_id_and_tip(self):
        self.orders.insert_order(1, 2, 25.5, "CARD", restaurant_id=7, tip=3.5, wallet_id=99)

        _, insert_params = self.cursor.execute.call_args.args
        self.assertEqual(insert_params, (1, 7, 2, 25.5, 3.5, None, "CARD", 99))

    def test_cash_payment_has_no_wallet_id(self):
        self.orders.insert_order(1, 2, 25.5, "CASH")

        _, insert_params = self.cursor.execute.call_args.args
        self.assertIsNone(insert_params[-1])

    def test_db_error_rolls_back_and_returns_false(self):
        self.cursor.execute.side_effect = Exception("db is down")

        result = self.orders.insert_order(1, 2, 25.5, "CASH")

        self.assertFalse(result)
        self.conn.rollback.assert_called_once()
        self.conn.commit.assert_not_called()


class TestGetUserOrdersUnit(unittest.TestCase):
    def setUp(self):
        self.conn = MagicMock()
        self.cursor = self.conn.cursor.return_value.__enter__.return_value
        self.orders = Orders(self.conn)

    def test_returns_raw_rows(self):
        rows = [(7, 42.0, 0, "PENDING", datetime(2026, 1, 2, 13, 30))]
        self.cursor.fetchall.return_value = rows

        result = self.orders.get_user_orders(1)

        self.assertEqual(result, rows)

    def test_no_orders_returns_empty_list(self):
        self.cursor.fetchall.return_value = []

        self.assertEqual(self.orders.get_user_orders(1), [])


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

    def test_returns_raw_rows(self):
        rows = [(7, 20.0, 3.0, "PENDING", datetime(2026, 1, 2, 13, 30), "no onions")]
        self.cursor.fetchall.return_value = rows

        self.assertEqual(self.orders.get_restaurant_orders(1), rows)


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

    def test_get_ready_orders_returns_raw_rows(self):
        rows = [(5, 12.5, 1, "Pizzaria", datetime(2026, 1, 1))]
        self.cursor.fetchall.return_value = rows

        result = self.orders.get_ready_orders_for_restaurants([1, 2])

        self.assertEqual(result, rows)
        query, params = self.cursor.execute.call_args.args
        self.assertIn("IN (%s,%s)", query)
        self.assertEqual(params, [1, 2])

    def test_claim_order_succeeds_when_row_matched(self):
        self.cursor.rowcount = 1

        result = self.orders.claim_order_for_delivery(5, 9)

        self.assertTrue(result)
        self.conn.commit.assert_called_once()

    def test_claim_order_fails_when_already_claimed(self):
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


class TestDeliveryIncomeRawUnit(unittest.TestCase):
    def setUp(self):
        self.conn = MagicMock()
        self.cursor = self.conn.cursor.return_value.__enter__.return_value
        self.orders = Orders(self.conn)

    def test_no_deliveries_returns_zeroed_counts(self):
        self.cursor.fetchone.return_value = (0, 0)

        self.assertEqual(self.orders.get_delivery_income_raw(9), (0, 0.0))

    def test_returns_count_and_tip_total(self):
        self.cursor.fetchone.return_value = (2, 5.0)

        self.assertEqual(self.orders.get_delivery_income_raw(9), (2, 5.0))


if __name__ == "__main__":
    unittest.main()
