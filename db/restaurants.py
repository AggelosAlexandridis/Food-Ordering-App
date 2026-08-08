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
            cur.execute("SELECT * FROM food WHERE restaurant_id=%s", (restaurant_id,))
            res = cur.fetchall()
        return [{"id": row[0], "text": f"{row[1]}: {float(row[2])}€"} for row in res]
