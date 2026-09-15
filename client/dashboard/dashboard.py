from kivy.app import App
from kivy.uix.screenmanager import Screen


class DashboardScreen(Screen):
    def on_enter(self):
        app = App.get_running_app()
        self.ids.rv.data = app.services.restaurants.list_restaurants()

        balance = app.services.wallet.get_balance(app.user_id)
        self.ids.balance_btn.text = f"Balance: {balance:.2f}€"

        profile = app.services.users.get_profile(app.user_id)
        self.ids.profile_name_label.text = profile["name"] or profile["username"]
