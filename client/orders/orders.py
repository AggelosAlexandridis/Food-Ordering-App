from kivy.app import App
from kivy.uix.screenmanager import Screen


class OrdersScreen(Screen):
    def on_enter(self):
        self.refresh_orders()

    def refresh_orders(self):
        app = App.get_running_app()
        self.ids.rv.data = app.db.orders.get_user_orders(app.user_id)
