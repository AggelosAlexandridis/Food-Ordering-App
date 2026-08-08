from kivy.app import App
from kivy.clock import Clock
from kivy.uix.screenmanager import Screen

POLL_INTERVAL = 5


class DeliveryDashboardScreen(Screen):
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
        restaurants = app.db.delivery.get_restaurants_for_delivery(app.user_id)
        restaurant_ids = [r["id"] for r in restaurants]
        ready_orders = app.db.orders.get_ready_orders_for_restaurants(restaurant_ids)

        counts = {}
        for order in ready_orders:
            counts[order["restaurant_id"]] = counts.get(order["restaurant_id"], 0) + 1

        for restaurant in restaurants:
            count = counts.get(restaurant["id"], 0)
            if count:
                restaurant["text"] = f"{restaurant['text']}  ·  {count} ready"

        self.ids.rv.data = restaurants
        self.ids.ready_btn.text = f"Ready: {len(ready_orders)}"
