from kivy.app import App
from kivy.uix.screenmanager import Screen


class DeliveryActiveScreen(Screen):
    def on_enter(self):
        self.refresh()

    def refresh(self):
        app = App.get_running_app()
        self.ids.rv.data = app.db.orders.get_delivery_orders(app.user_id)
