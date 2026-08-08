from kivy.app import App
from kivy.uix.screenmanager import Screen


class RestaurantScreen(Screen):
    def on_enter(self):
        app = App.get_running_app()
        self.ids.rv.data = app.db.restaurants.get_menu(app.selected_restaurant_id)
