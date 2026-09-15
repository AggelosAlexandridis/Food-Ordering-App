import unittest
from unittest.mock import MagicMock

from db.restaurants import Restaurants


class TestRestaurantsUnit(unittest.TestCase):

    def setUp(self):
        self.conn = MagicMock()
        self.cursor = self.conn.cursor.return_value.__enter__.return_value
        self.restaurants = Restaurants(self.conn)

    def test_get_restaurants_returns_raw_rows(self):
        self.cursor.fetchall.return_value = [(1, "Pizza Place"), (2, "Sushi Bar")]

        result = self.restaurants.get_restaurants()

        self.assertEqual(result, [(1, "Pizza Place"), (2, "Sushi Bar")])

    def test_get_restaurants_empty(self):
        self.cursor.fetchall.return_value = []

        self.assertEqual(self.restaurants.get_restaurants(), [])

    def test_get_menu_returns_raw_rows(self):
        self.cursor.fetchall.return_value = [(10, "Margherita", 8.5)]

        result = self.restaurants.get_menu(1)

        self.assertEqual(result, [(10, "Margherita", 8.5)])

    def test_get_menu_filters_by_restaurant_id_and_availability(self):
        self.cursor.fetchall.return_value = []

        self.restaurants.get_menu(42)

        query, params = self.cursor.execute.call_args.args
        self.assertIn("WHERE restaurant_id=%s AND available=1", query)
        self.assertEqual(params, (42,))

    def test_get_menu_for_unknown_restaurant_returns_empty(self):
        self.cursor.fetchall.return_value = []

        self.assertEqual(self.restaurants.get_menu(999999), [])

    def test_get_full_menu_returns_raw_rows_including_unavailable(self):
        self.cursor.fetchall.return_value = [
            (10, "Margherita", 8.5, 1),
            (11, "Quattro Stagioni", 9.0, 0),
        ]

        result = self.restaurants.get_full_menu(1)

        self.assertEqual(result, [
            (10, "Margherita", 8.5, 1),
            (11, "Quattro Stagioni", 9.0, 0),
        ])

    def test_get_full_menu_does_not_filter_by_availability(self):
        self.cursor.fetchall.return_value = []

        self.restaurants.get_full_menu(42)

        query, params = self.cursor.execute.call_args.args
        self.assertNotIn("available=1", query)
        self.assertIn("WHERE restaurant_id=%s", query)
        self.assertEqual(params, (42,))

    def test_get_items_by_ids_returns_raw_rows(self):
        self.cursor.fetchall.return_value = [(10, "Margherita", 1), (11, "Calzone", 0)]

        result = self.restaurants.get_items_by_ids([10, 11])

        self.assertEqual(result, [(10, "Margherita", 1), (11, "Calzone", 0)])
        query, params = self.cursor.execute.call_args.args
        self.assertIn("WHERE id IN (%s,%s)", query)
        self.assertEqual(params, [10, 11])

    def test_get_items_by_ids_empty_list_short_circuits(self):
        result = self.restaurants.get_items_by_ids([])

        self.assertEqual(result, [])
        self.cursor.execute.assert_not_called()

    def test_toggle_food_availability_scopes_by_restaurant_and_commits(self):
        self.cursor.rowcount = 1

        result = self.restaurants.toggle_food_availability(10, restaurant_id=1)

        self.assertTrue(result)
        query, params = self.cursor.execute.call_args.args
        self.assertIn("WHERE id = %s AND restaurant_id = %s", query)
        self.assertEqual(params, (10, 1))
        self.conn.commit.assert_called_once()

    def test_toggle_food_availability_not_found_rolls_back(self):
        self.cursor.rowcount = 0

        result = self.restaurants.toggle_food_availability(10, restaurant_id=1)

        self.assertFalse(result)
        self.conn.rollback.assert_called_once()
        self.conn.commit.assert_not_called()

    def test_toggle_food_availability_rolls_back_on_db_error(self):
        self.cursor.execute.side_effect = Exception("db error")

        result = self.restaurants.toggle_food_availability(10, restaurant_id=1)

        self.assertFalse(result)
        self.conn.rollback.assert_called_once()

    def test_add_food_item_commits_and_returns_true(self):
        result = self.restaurants.add_food_item(1, "Margherita", 8.5)

        self.assertTrue(result)
        self.conn.commit.assert_called_once()
        query, params = self.cursor.execute.call_args.args
        self.assertIn("INSERT INTO food", query)
        self.assertEqual(params, ("Margherita", 8.5, 1))

    def test_add_food_item_rolls_back_on_db_error(self):
        self.cursor.execute.side_effect = Exception("db error")

        result = self.restaurants.add_food_item(1, "Margherita", 8.5)

        self.assertFalse(result)
        self.conn.rollback.assert_called_once()
        self.conn.commit.assert_not_called()

    def test_update_food_price_scopes_by_restaurant_and_commits(self):
        self.cursor.rowcount = 1

        result = self.restaurants.update_food_price(10, restaurant_id=1, price=9.5)

        self.assertTrue(result)
        query, params = self.cursor.execute.call_args.args
        self.assertIn("WHERE id = %s AND restaurant_id = %s", query)
        self.assertEqual(params, (9.5, 10, 1))
        self.conn.commit.assert_called_once()

    def test_update_food_price_not_found_rolls_back(self):
        self.cursor.rowcount = 0

        result = self.restaurants.update_food_price(10, restaurant_id=1, price=9.5)

        self.assertFalse(result)
        self.conn.rollback.assert_called_once()

    def test_delete_food_item_scopes_by_restaurant_and_commits(self):
        self.cursor.rowcount = 1

        result = self.restaurants.delete_food_item(10, restaurant_id=1)

        self.assertTrue(result)
        query, params = self.cursor.execute.call_args.args
        self.assertIn("WHERE id = %s AND restaurant_id = %s", query)
        self.assertEqual(params, (10, 1))
        self.conn.commit.assert_called_once()

    def test_delete_food_item_not_found_rolls_back(self):
        self.cursor.rowcount = 0

        result = self.restaurants.delete_food_item(10, restaurant_id=1)

        self.assertFalse(result)
        self.conn.rollback.assert_called_once()
        self.conn.commit.assert_not_called()

    def test_delete_food_item_rolls_back_on_db_error(self):
        self.cursor.execute.side_effect = Exception("db error")

        result = self.restaurants.delete_food_item(10, restaurant_id=1)

        self.assertFalse(result)
        self.conn.rollback.assert_called_once()


if __name__ == "__main__":
    unittest.main()
