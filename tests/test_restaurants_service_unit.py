import unittest
from unittest.mock import MagicMock

from services.restaurants import Restaurants


class TestListRestaurantsUnit(unittest.TestCase):
    def test_maps_id_and_name(self):
        db = MagicMock()
        db.restaurants.get_restaurants.return_value = [(1, "Pizza Place"), (2, "Sushi Bar")]
        service = Restaurants(db)

        result = service.list_restaurants()

        self.assertEqual(result, [
            {"id": 1, "text": "Pizza Place"},
            {"id": 2, "text": "Sushi Bar"},
        ])


class TestGetMenuUnit(unittest.TestCase):
    def test_formats_name_and_price(self):
        db = MagicMock()
        db.restaurants.get_menu.return_value = [(10, "Margherita", 8.5)]
        service = Restaurants(db)

        result = service.get_menu(1)

        self.assertEqual(result, [{"id": 10, "text": "Margherita: 8.5€"}])


class TestGetFullMenuUnit(unittest.TestCase):
    def test_includes_unavailable_items_with_flag(self):
        db = MagicMock()
        db.restaurants.get_full_menu.return_value = [
            (10, "Margherita", 8.5, 1),
            (11, "Quattro Stagioni", 9.0, 0),
        ]
        service = Restaurants(db)

        result = service.get_full_menu(1)

        self.assertEqual(result, [
            {"id": 10, "text": "Margherita: 8.5€", "price": 8.5, "available": True},
            {"id": 11, "text": "Quattro Stagioni: 9.0€", "price": 9.0, "available": False},
        ])


class TestFindUnavailableCartItemsUnit(unittest.TestCase):
    def test_returns_only_unavailable_items(self):
        db = MagicMock()
        db.restaurants.get_items_by_ids.return_value = [(10, "Margherita", 1), (11, "Calzone", 0)]
        service = Restaurants(db)

        result = service.find_unavailable_cart_items([{"id": 10, "quantity": 1}, {"id": 11, "quantity": 2}])

        self.assertEqual(result, [{"id": 11, "name": "Calzone"}])


class TestAddFoodItemUnit(unittest.TestCase):
    def setUp(self):
        self.db = MagicMock()
        self.service = Restaurants(self.db)

    def test_rejects_empty_name(self):
        success, error = self.service.add_food_item(1, "  ", "8.5")

        self.assertFalse(success)
        self.assertIn("name for the dish", error)
        self.db.restaurants.add_food_item.assert_not_called()

    def test_rejects_non_numeric_price(self):
        success, error = self.service.add_food_item(1, "Margherita", "abc")

        self.assertFalse(success)
        self.assertIn("valid price", error)

    def test_rejects_zero_or_negative_price(self):
        success, error = self.service.add_food_item(1, "Margherita", "0")

        self.assertFalse(success)
        self.assertIn("valid price", error)

    def test_valid_item_is_saved_rounded_to_cents(self):
        self.db.restaurants.add_food_item.return_value = True

        success, error = self.service.add_food_item(1, " Margherita ", "8.567")

        self.assertTrue(success)
        self.assertIsNone(error)
        self.db.restaurants.add_food_item.assert_called_once_with(1, "Margherita", 8.57)

    def test_db_failure_returns_friendly_error(self):
        self.db.restaurants.add_food_item.return_value = False

        success, error = self.service.add_food_item(1, "Margherita", "8.5")

        self.assertFalse(success)
        self.assertIn("Error saving dish", error)


class TestUpdateFoodPriceUnit(unittest.TestCase):
    def setUp(self):
        self.db = MagicMock()
        self.service = Restaurants(self.db)

    def test_rejects_invalid_price(self):
        success, error = self.service.update_food_price(10, 1, "-5")

        self.assertFalse(success)
        self.assertIn("valid price", error)
        self.db.restaurants.update_food_price.assert_not_called()

    def test_valid_price_is_saved(self):
        self.db.restaurants.update_food_price.return_value = True

        success, error = self.service.update_food_price(10, 1, "9.5")

        self.assertTrue(success)
        self.db.restaurants.update_food_price.assert_called_once_with(10, 1, 9.5)

    def test_db_failure_returns_friendly_error(self):
        self.db.restaurants.update_food_price.return_value = False

        success, error = self.service.update_food_price(10, 1, "9.5")

        self.assertFalse(success)
        self.assertIn("Error saving price", error)


class TestToggleAndDeleteUnit(unittest.TestCase):
    def test_toggle_delegates_to_repository(self):
        db = MagicMock()
        db.restaurants.toggle_food_availability.return_value = True
        service = Restaurants(db)

        self.assertTrue(service.toggle_food_availability(10, 1))

    def test_delete_delegates_to_repository(self):
        db = MagicMock()
        db.restaurants.delete_food_item.return_value = True
        service = Restaurants(db)

        self.assertTrue(service.delete_food_item(10, 1))


if __name__ == "__main__":
    unittest.main()
