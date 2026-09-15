class Restaurants:
    def __init__(self, db):
        self.db = db

    def list_restaurants(self):
        rows = self.db.restaurants.get_restaurants()
        return [{"id": row[0], "text": row[1]} for row in rows]

    def get_restaurant(self, restaurant_id):
        return self.db.restaurants.get_restaurant(restaurant_id)

    def get_menu(self, restaurant_id):
        rows = self.db.restaurants.get_menu(restaurant_id)
        return [{"id": row[0], "text": f"{row[1]}: {float(row[2])}€"} for row in rows]

    def get_full_menu(self, restaurant_id):
        rows = self.db.restaurants.get_full_menu(restaurant_id)
        return [
            {
                "id": row[0],
                "text": f"{row[1]}: {float(row[2])}€",
                "price": float(row[2]),
                "available": bool(row[3]),
            }
            for row in rows
        ]

    def find_unavailable_cart_items(self, cart):
        """[{'id', 'name'}, ...] for cart items that are no longer available."""
        ids = [item["id"] for item in cart]
        items = self.db.restaurants.get_items_by_ids(ids)
        return [
            {"id": row[0], "name": row[1]}
            for row in items
            if not bool(row[2])
        ]

    def add_food_item(self, restaurant_id, name, price_text):
        name = name.strip()
        if not name:
            return False, "Enter a name for the dish."

        try:
            price = float(price_text.strip())
            if price <= 0:
                raise ValueError
        except ValueError:
            return False, "Enter a valid price greater than 0."

        success = self.db.restaurants.add_food_item(restaurant_id, name, round(price, 2))
        if not success:
            return False, "Error saving dish to database."
        return True, None

    def update_food_price(self, food_id, restaurant_id, price_text):
        try:
            price = float(price_text.strip())
            if price <= 0:
                raise ValueError
        except ValueError:
            return False, "Enter a valid price greater than 0."

        success = self.db.restaurants.update_food_price(food_id, restaurant_id, round(price, 2))
        if not success:
            return False, "Error saving price."
        return True, None

    def toggle_food_availability(self, food_id, restaurant_id):
        return self.db.restaurants.toggle_food_availability(food_id, restaurant_id)

    def delete_food_item(self, food_id, restaurant_id):
        return self.db.restaurants.delete_food_item(food_id, restaurant_id)
