import unittest
from unittest.mock import MagicMock

from db.restaurants import Restaurants


class TestRestaurantsUnit(unittest.TestCase):
    """Pure unit tests: the DB connection/cursor are mocked, no real DB is touched."""

    def setUp(self):
        self.conn = MagicMock()
        self.cursor = self.conn.cursor.return_value.__enter__.return_value
        self.restaurants = Restaurants(self.conn)

    def test_get_restaurants_maps_id_and_name(self):
        self.cursor.fetchall.return_value = [(1, "Pizza Place"), (2, "Sushi Bar")]

        result = self.restaurants.get_restaurants()

        self.assertEqual(result, [
            {"id": 1, "text": "Pizza Place"},
            {"id": 2, "text": "Sushi Bar"},
        ])

    def test_get_restaurants_empty(self):
        self.cursor.fetchall.return_value = []

        self.assertEqual(self.restaurants.get_restaurants(), [])

    def test_get_menu_formats_name_and_price(self):
        self.cursor.fetchall.return_value = [(10, "Margherita", 8.5, 1)]

        result = self.restaurants.get_menu(1)

        self.assertEqual(result, [{"id": 10, "text": "Margherita: 8.5€"}])

    def test_get_menu_filters_by_restaurant_id(self):
        self.cursor.fetchall.return_value = []

        self.restaurants.get_menu(42)

        query, params = self.cursor.execute.call_args.args
        self.assertIn("WHERE restaurant_id=%s", query)
        self.assertEqual(params, (42,))

    def test_get_menu_for_unknown_restaurant_returns_empty(self):
        self.cursor.fetchall.return_value = []

        self.assertEqual(self.restaurants.get_menu(999999), [])


if __name__ == "__main__":
    unittest.main()
