import re
from datetime import date

from kivy.app import App
from kivy.uix.screenmanager import Screen

CARD_NUMBER_RE = re.compile(r"^\d{16}$")
CVV_RE = re.compile(r"^\d{3,4}$")
EXPIRY_RE = re.compile(r"^(0[1-9]|1[0-2])/(\d{2})$")


class CardsScreen(Screen):
    selected_type = "VISA"

    def on_enter(self):
        self.refresh_cards()
        self.reset_form()

    def refresh_cards(self):
        app = App.get_running_app()
        self.ids.rv.data = app.db.cards.get_cards(app.user_id)

    def reset_form(self):
        self.ids.holder_input.text = ""
        self.ids.number_input.text = ""
        self.ids.cvv_input.text = ""
        self.ids.expiry_input.text = ""
        self.ids.error_label.text = ""
        self.select_type("VISA")

    def select_type(self, card_type):
        self.selected_type = card_type
        self.ids.visa_pill.selected = card_type == "VISA"
        self.ids.mastercard_pill.selected = card_type == "MASTERCARD"

    def save_card(self):
        app = App.get_running_app()

        holder = self.ids.holder_input.text.strip()
        number = self.ids.number_input.text.strip()
        cvv = self.ids.cvv_input.text.strip()
        expiry = self.ids.expiry_input.text.strip()

        if not holder:
            self.ids.error_label.text = "Enter the name on the card."
            return

        if not CARD_NUMBER_RE.match(number):
            self.ids.error_label.text = "Card number must be exactly 16 digits."
            return

        if not CVV_RE.match(cvv):
            self.ids.error_label.text = "CVV must be 3 or 4 digits."
            return

        match = EXPIRY_RE.match(expiry)
        if not match:
            self.ids.error_label.text = "Expiry must be in MM/YY format."
            return

        month, year_suffix = int(match.group(1)), int(match.group(2))
        expiration_date = date(2000 + year_suffix, month, 1)
        if expiration_date < date.today().replace(day=1):
            self.ids.error_label.text = "This card has already expired."
            return

        success = app.db.cards.add_card(
            app.user_id, number, cvv, holder, expiration_date, self.selected_type
        )
        if success:
            self.reset_form()
            self.refresh_cards()
        else:
            self.ids.error_label.text = "Error saving card to database."
