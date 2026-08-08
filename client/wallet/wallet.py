from kivy.app import App
from kivy.uix.screenmanager import Screen


class WalletScreen(Screen):
    def on_enter(self):
        app = App.get_running_app()
        balance = app.db.wallet.get_balance(app.user_id)

        self.ids.balance_label.text = f"{balance:.2f}€"
        self.ids.amount_input.text = ""
        self.ids.msg_label.text = ""
