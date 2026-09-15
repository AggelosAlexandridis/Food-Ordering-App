import re
from datetime import date

CARD_NUMBER_RE = re.compile(r"^\d{16}$")
CVV_RE = re.compile(r"^\d{3,4}$")
EXPIRY_RE = re.compile(r"^(0[1-9]|1[0-2])/(\d{2})$")


class Cards:
    def __init__(self, db):
        self.db = db

    def list_cards(self, user_id):
        rows = self.db.cards.get_cards(user_id)
        return [
            {
                "id": row[0],
                "card_number": row[1],
                "card_holder_name": row[2],
                "expiration_date": row[3],
                "type": row[4],
                "text": f"{row[4].title()} •••• {row[1][-4:]}  ·  exp {row[3].strftime('%m/%y')}",
            }
            for row in rows
        ]

    def add_card(self, user_id, holder, number, cvv, expiry, card_type):
        holder = holder.strip()
        number = number.strip()
        cvv = cvv.strip()
        expiry = expiry.strip()

        if not holder:
            return False, "Enter the name on the card."

        if not CARD_NUMBER_RE.match(number):
            return False, "Card number must be exactly 16 digits."

        if not CVV_RE.match(cvv):
            return False, "CVV must be 3 or 4 digits."

        match = EXPIRY_RE.match(expiry)
        if not match:
            return False, "Expiry must be in MM/YY format."

        month, year_suffix = int(match.group(1)), int(match.group(2))
        expiration_date = date(2000 + year_suffix, month, 1)
        if expiration_date < date.today().replace(day=1):
            return False, "This card has already expired."

        success = self.db.cards.add_card(user_id, number, cvv, holder, expiration_date, card_type)
        if not success:
            return False, "Error saving card to database."
        return True, None

    def delete_card(self, user_id, card_id):
        return self.db.cards.delete_card(user_id, card_id)
