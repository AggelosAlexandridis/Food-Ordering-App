from kivy.app import App
from kivy.uix.screenmanager import Screen


class AddressScreen(Screen):
    def on_enter(self):
        self.refresh_addresses()

    def refresh_addresses(self):
        app = App.get_running_app()
        app.cached_addresses = app.services.addresses.list_addresses(app.user_id)
        self.ids.rv.data = app.cached_addresses
