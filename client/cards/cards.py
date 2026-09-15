from kivy.app import App
from kivy.uix.screenmanager import Screen


class CardsScreen(Screen):
    selected_type = "VISA"

    def on_enter(self):
        self.refresh_cards()
        self.reset_form()

    def refresh_cards(self):
        app = App.get_running_app()
        self.ids.rv.data = app.services.cards.list_cards(app.user_id)

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

        holder = self.ids.holder_input.text
        number = self.ids.number_input.text
        cvv = self.ids.cvv_input.text
        expiry = self.ids.expiry_input.text

        success, error = app.services.cards.add_card(
            app.user_id, holder, number, cvv, expiry, self.selected_type
        )
        if success:
            self.reset_form()
            self.refresh_cards()
        else:
            self.ids.error_label.text = error
