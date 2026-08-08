from kivy.app import App
from kivy.clock import Clock
from kivy.uix.screenmanager import Screen

POLL_INTERVAL = 5


class DeliveryOrdersScreen(Screen):
    restaurant_id = None

    def on_enter(self):
        self.ids.error_label.text = ""
        self.refresh()
        self._poll_event = Clock.schedule_interval(lambda dt: self.refresh(), POLL_INTERVAL)

    def on_leave(self):
        event = getattr(self, "_poll_event", None)
        if event:
            event.cancel()
            self._poll_event = None

    def refresh(self):
        app = App.get_running_app()

        if self.restaurant_id:
            restaurant_ids = [self.restaurant_id]
            restaurant = app.db.restaurants.get_restaurant(self.restaurant_id)
            self.ids.title_label.text = restaurant["name"] if restaurant else "Ready Orders"
        else:
            restaurants = app.db.delivery.get_restaurants_for_delivery(app.user_id)
            restaurant_ids = [r["id"] for r in restaurants]
            self.ids.title_label.text = "All Ready Orders"

        self.ids.rv.data = app.db.orders.get_ready_orders_for_restaurants(restaurant_ids)
