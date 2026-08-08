import random

# Excludes 0/O and 1/I/L, which are easy to misread when a code is copied
# by eye between two windows (e.g. a chef's screen and a delivery person's).
CODE_ALPHABET = "ABCDEFGHJKMNPQRSTUVWXYZ23456789"


def generate_code(length=8):
    return "".join(random.choices(CODE_ALPHABET, k=length))


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
            res = cur.fetchall()
        return [{"id": row[0], "text": row[1]} for row in res]

    def generate_invite_code(self, restaurant_id, created_by):
        code = generate_code()
        try:
            with self.conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO restaurant_invite_codes (restaurant_id, code, created_by) VALUES (%s, %s, %s)",
                    (restaurant_id, code, created_by),
                )
            self.conn.commit()
            return code
        except Exception as e:
            print(f"Error generating invite code: {e}")
            self.conn.rollback()
            return None

    def redeem_invite_code(self, code, delivery_user_id):
        clean_code = code.strip().upper()

        with self.conn.cursor() as cur:
            cur.execute(
                "SELECT id, restaurant_id, used_by FROM restaurant_invite_codes WHERE code = %s",
                (clean_code,),
            )
            row = cur.fetchone()

        if not row:
            return None, "That code doesn't exist. Double-check it and try again."

        code_id, restaurant_id, used_by = row
        if used_by is not None:
            return None, "That code has already been used."

        with self.conn.cursor() as cur:
            cur.execute(
                "SELECT 1 FROM delivery_restaurants WHERE delivery_user_id = %s AND restaurant_id = %s",
                (delivery_user_id, restaurant_id),
            )
            if cur.fetchone():
                return None, "You're already registered to that restaurant."

        try:
            with self.conn.cursor() as cur:
                # The connection defaults to autocommit; these two writes
                # (burn the code, create the link) must succeed or fail
                # together, so wrap them in an explicit transaction.
                cur.execute("START TRANSACTION")
                cur.execute(
                    "UPDATE restaurant_invite_codes SET used_by = %s, used_at = NOW() WHERE id = %s AND used_by IS NULL",
                    (delivery_user_id, code_id),
                )
                if cur.rowcount == 0:
                    self.conn.rollback()
                    return None, "This code was just used by someone else."

                cur.execute(
                    "INSERT INTO delivery_restaurants (delivery_user_id, restaurant_id) VALUES (%s, %s)",
                    (delivery_user_id, restaurant_id),
                )
            self.conn.commit()
            return restaurant_id, None
        except Exception as e:
            print(f"Error redeeming invite code: {e}")
            self.conn.rollback()
            return None, "Error redeeming code. Please try again."
