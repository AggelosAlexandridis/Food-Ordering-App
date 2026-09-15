import random

# Excludes 0/O and 1/I/L, which are easy to misread when a code is copied
# by eye between two windows (e.g. a chef's screen and a delivery person's).
CODE_ALPHABET = "ABCDEFGHJKMNPQRSTUVWXYZ23456789"


def generate_code(length=8):
    return "".join(random.choices(CODE_ALPHABET, k=length))


class Delivery:
    def __init__(self, db):
        self.db = db

    def list_restaurants_for_delivery(self, delivery_user_id):
        rows = self.db.delivery.get_restaurants_for_delivery(delivery_user_id)
        return [{"id": row[0], "text": row[1]} for row in rows]

    def generate_invite_code(self, restaurant_id, created_by):
        code = generate_code()
        if not self.db.delivery.create_invite_code(restaurant_id, code, created_by):
            return None
        return code

    def redeem_invite_code(self, code_text, delivery_user_id):
        clean_code = (code_text or "").strip()
        if not clean_code:
            return None, "Enter a code first."

        clean_code = clean_code.upper()
        row = self.db.delivery.find_invite_code(clean_code)
        if not row:
            return None, "That code doesn't exist. Double-check it and try again."

        code_id, restaurant_id, used_by = row
        if used_by is not None:
            return None, "That code has already been used."

        if self.db.delivery.is_delivery_linked(delivery_user_id, restaurant_id):
            return None, "You're already registered to that restaurant."

        claimed = self.db.delivery.redeem_invite_code_atomic(code_id, restaurant_id, delivery_user_id)
        if not claimed:
            return None, "This code was just used by someone else."

        return restaurant_id, None
