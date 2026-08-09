from kivy.app import App
from kivy.clock import Clock
from kivy.uix.screenmanager import Screen

POLL_INTERVAL = 5


class RestaurantScreen(Screen):
    def on_enter(self):
        self.refresh()
        self._poll_event = Clock.schedule_interval(lambda dt: self.refresh(), POLL_INTERVAL)

    def on_leave(self):
        event = getattr(self, "_poll_event", None)
        if event:
            event.cancel()
            self._poll_event = None

    def refresh(self):
        app = App.get_running_app()
        self.ids.rv.data = app.db.restaurants.get_menu(app.selected_restaurant_id)
