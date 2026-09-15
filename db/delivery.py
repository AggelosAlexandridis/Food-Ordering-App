class Delivery:
    def __init__(self, conn):
        self.conn = conn

    def get_restaurants_for_delivery(self, delivery_user_id):
        with self.conn.cursor() as cur:
            cur.execute(
                """
                SELECT r.id, r.name
                FROM delivery_restaurants dr
                JOIN restaurants r ON r.id = dr.restaurant_id
                WHERE dr.delivery_user_id = %s
                ORDER BY r.name
                """,
                (delivery_user_id,),
            )
            return cur.fetchall()

    def create_invite_code(self, restaurant_id, code, created_by):
        try:
            with self.conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO restaurant_invite_codes (restaurant_id, code, created_by) VALUES (%s, %s, %s)",
                    (restaurant_id, code, created_by),
                )
            self.conn.commit()
            return True
        except Exception as e:
            print(f"Error generating invite code: {e}")
            self.conn.rollback()
            return False

    def find_invite_code(self, code):
        with self.conn.cursor() as cur:
            cur.execute(
                "SELECT id, restaurant_id, used_by FROM restaurant_invite_codes WHERE code = %s",
                (code,),
            )
            return cur.fetchone()

    def is_delivery_linked(self, delivery_user_id, restaurant_id):
        with self.conn.cursor() as cur:
            cur.execute(
                "SELECT 1 FROM delivery_restaurants WHERE delivery_user_id = %s AND restaurant_id = %s",
                (delivery_user_id, restaurant_id),
            )
            return cur.fetchone() is not None

    def redeem_invite_code_atomic(self, code_id, restaurant_id, delivery_user_id):
        try:
            with self.conn.cursor() as cur:
                cur.execute("START TRANSACTION")
                cur.execute(
                    "UPDATE restaurant_invite_codes SET used_by = %s, used_at = NOW() WHERE id = %s AND used_by IS NULL",
                    (delivery_user_id, code_id),
                )
                if cur.rowcount == 0:
                    self.conn.rollback()
                    return False

                cur.execute(
                    "INSERT INTO delivery_restaurants (delivery_user_id, restaurant_id) VALUES (%s, %s)",
                    (delivery_user_id, restaurant_id),
                )
            self.conn.commit()
            return True
        except Exception as e:
            print(f"Error redeeming invite code: {e}")
            self.conn.rollback()
            return False
