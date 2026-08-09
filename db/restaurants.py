class Restaurants:
    def __init__(self, conn):
        self.conn = conn

    def get_restaurants(self):
        with self.conn.cursor() as cur:
            cur.execute("SELECT * FROM restaurants")
            res = cur.fetchall()
        return [{"id": row[0], "text": row[1]} for row in res]

    def get_restaurant(self, restaurant_id):
        with self.conn.cursor() as cur:
            cur.execute("SELECT id, name FROM restaurants WHERE id = %s", (restaurant_id,))
            row = cur.fetchone()
        return {"id": row[0], "name": row[1]} if row else None

    def get_menu(self, restaurant_id):
        with self.conn.cursor() as cur:
            cur.execute(
                "SELECT * FROM food WHERE restaurant_id=%s AND available=1", (restaurant_id,)
            )
            res = cur.fetchall()
        return [{"id": row[0], "text": f"{row[1]}: {float(row[2])}€"} for row in res]

    def get_full_menu(self, restaurant_id):
        with self.conn.cursor() as cur:
            cur.execute(
                "SELECT id, name, price, available FROM food WHERE restaurant_id=%s",
                (restaurant_id,),
            )
            res = cur.fetchall()
        return [
            {
                "id": row[0],
                "text": f"{row[1]}: {float(row[2])}€",
                "available": bool(row[3]),
            }
            for row in res
        ]

    def get_items_by_ids(self, food_ids):
        if not food_ids:
            return []

        placeholders = ",".join(["%s"] * len(food_ids))
        with self.conn.cursor() as cur:
            cur.execute(
                f"SELECT id, name, available FROM food WHERE id IN ({placeholders})",
                food_ids,
            )
            res = cur.fetchall()
        return [{"id": row[0], "name": row[1], "available": bool(row[2])} for row in res]

    def toggle_food_availability(self, food_id, restaurant_id):
        try:
            with self.conn.cursor() as cur:
                cur.execute(
                    "UPDATE food SET available = NOT available WHERE id = %s AND restaurant_id = %s",
                    (food_id, restaurant_id),
                )
                updated = cur.rowcount == 1

            if updated:
                self.conn.commit()
            else:
                self.conn.rollback()
            return updated
        except Exception as e:
            print(f"Error toggling food availability: {e}")
            self.conn.rollback()
            return False

    def add_food_item(self, restaurant_id, name, price):
        try:
            with self.conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO food (name, price, restaurant_id) VALUES (%s, %s, %s)",
                    (name, price, restaurant_id),
                )
            self.conn.commit()
            return True
        except Exception as e:
            print(f"Error adding food item: {e}")
            self.conn.rollback()
            return False

    def delete_food_item(self, food_id, restaurant_id):
        try:
            with self.conn.cursor() as cur:
                cur.execute(
                    "DELETE FROM food WHERE id = %s AND restaurant_id = %s",
                    (food_id, restaurant_id),
                )
                deleted = cur.rowcount == 1
            if deleted:
                self.conn.commit()
            else:
                self.conn.rollback()
            return deleted
        except Exception as e:
            print(f"Error deleting food item: {e}")
            self.conn.rollback()
            return False
