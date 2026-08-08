from kivy.app import App
from kivy.uix.screenmanager import Screen


class DashboardScreen(Screen):
    def on_enter(self):
        app = App.get_running_app()
        self.ids.rv.data = app.db.restaurants.get_restaurants()

        balance = app.db.wallet.get_balance(app.user_id)
        self.ids.balance_btn.text = f"Balance: {balance:.2f}€"

        profile = app.db.users.get_profile(app.user_id)
        self.ids.profile_name_label.text = profile["name"] or profile["username"]
