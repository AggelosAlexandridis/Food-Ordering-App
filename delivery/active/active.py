from kivy.app import App
from kivy.uix.screenmanager import Screen


class DeliveryActiveScreen(Screen):
    def on_enter(self):
        self.refresh()

    def refresh(self):
        app = App.get_running_app()
        self.ids.rv.data = app.services.orders.list_active_deliveries(app.user_id)
