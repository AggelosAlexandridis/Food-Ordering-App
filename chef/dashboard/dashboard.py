from kivy.animation import Animation
from kivy.app import App
from kivy.clock import Clock
from kivy.graphics import Color, RoundedRectangle
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.screenmanager import Screen

from common.widgets import DANGER

POLL_INTERVAL = 5


class ChefDashboardScreen(Screen):
    restaurant_id = None

    def on_enter(self):
        app = App.get_running_app()
        self.restaurant_id = app.db.users.get_restaurant_id(app.user_id)

        restaurant = app.db.restaurants.get_restaurant(self.restaurant_id) if self.restaurant_id else None
        self.ids.restaurant_label.text = restaurant["name"] if restaurant else "Your restaurant"

        self._known_pending_ids = None
        self._pill_idle_color = None
        self.refresh()
        self._poll_event = Clock.schedule_interval(lambda dt: self.refresh(), POLL_INTERVAL)

    def on_leave(self):
        event = getattr(self, "_poll_event", None)
        if event:
            event.cancel()
            self._poll_event = None
        Animation.cancel_all(self.ids.new_orders_btn)

    def refresh(self):
        app = App.get_running_app()
        if not self.restaurant_id:
            return

        orders = app.db.orders.get_restaurant_orders(self.restaurant_id)
        self.ids.rv.data = orders

        pending_count = sum(1 for o in orders if o["status"] == "PENDING")
        self.ids.new_orders_btn.text = f"New Orders: {pending_count}"

        if self._pill_idle_color is None:
            self._pill_idle_color = list(self.ids.new_orders_btn.color)

        current_pending_ids = {o["id"] for o in orders if o["status"] == "PENDING"}
        if self._known_pending_ids is not None and current_pending_ids - self._known_pending_ids:
            self._flash_new_orders()
        self._known_pending_ids = current_pending_ids

    def _flash_new_orders(self):
        pill = self.ids.new_orders_btn
        Animation.cancel_all(pill)
        anim = Animation(color=DANGER, duration=0.25) + Animation(color=self._pill_idle_color, duration=0.25)
        anim.start(pill)

    def open_invite_code_popup(self):
        app = App.get_running_app()
        code = app.db.delivery.generate_invite_code(self.restaurant_id, app.user_id)

        content = BoxLayout(orientation="vertical", padding=24, spacing=14)
        with content.canvas.before:
            Color(1, 1, 1, 1)
            card = RoundedRectangle(pos=content.pos, size=content.size, radius=[18])

        def sync(*_):
            card.pos = content.pos
            card.size = content.size

        content.bind(pos=sync, size=sync)

        content.add_widget(Label(
            text="Delivery invite code",
            color=(0.11, 0.11, 0.118, 1),
            bold=True,
            font_size="18sp",
            size_hint_y=None,
            height=28,
        ))

        if code:
            message = f"Share this one-time code with a delivery person:\n\n{code}"
        else:
            message = "Could not generate a code. Please try again."

        content.add_widget(Label(
            text=message,
            color=(0.35, 0.35, 0.37, 1),
            halign="center",
            valign="middle",
            text_size=(312, None),
        ))

        from common.widgets import ActionBtn, PRIMARY

        close_btn = ActionBtn(text="Done", btn_color=PRIMARY, size_hint_y=None, height=50)

        popup = Popup(
            title="",
            separator_height=0,
            content=content,
            size_hint=(None, None),
            size=(360, 260),
            auto_dismiss=False,
            background_color=(0, 0, 0, 0),
        )
        close_btn.bind(on_release=popup.dismiss)
        content.add_widget(close_btn)
        popup.open()
