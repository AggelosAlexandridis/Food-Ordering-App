from kivy.app import App
from kivy.uix.screenmanager import Screen


class ChefMenuScreen(Screen):
    restaurant_id = None

    def on_enter(self):
        app = App.get_running_app()
        self.restaurant_id = app.services.users.get_restaurant_id(app.user_id)
        self.reset_form()
        self.refresh_menu()

    def refresh_menu(self):
        app = App.get_running_app()
        if not self.restaurant_id:
            self.ids.rv.data = []
            return
        self.ids.rv.data = app.services.restaurants.get_full_menu(self.restaurant_id)

    def reset_form(self):
        self.ids.name_input.text = ""
        self.ids.price_input.text = ""
        self.ids.error_label.text = ""

    def save_item(self):
        app = App.get_running_app()

        name = self.ids.name_input.text
        price_text = self.ids.price_input.text

        success, error = app.services.restaurants.add_food_item(self.restaurant_id, name, price_text)
        if success:
            self.reset_form()
            self.refresh_menu()
        else:
            self.ids.error_label.text = error
