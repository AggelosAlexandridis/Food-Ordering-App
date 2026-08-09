import re

from kivy.app import App
from kivy.lang import Builder
from kivy.properties import StringProperty
from kivy.graphics import Color, RoundedRectangle
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.screenmanager import SlideTransition
from kivy.uix.textinput import TextInput

from common.widgets import DANGER, PRIMARY, ActionBtn, GhostBtn
from db import DBManager

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

# Unused directly, but importing these modules defines their Screen
# subclasses so Kivy can resolve them when common/root.kv is built.
from common.login.login import LoginScreen  # noqa: F401
from common.register.register import RegisterScreen  # noqa: F401
from client.dashboard.dashboard import DashboardScreen  # noqa: F401
from client.restaurant.restaurant import RestaurantScreen  # noqa: F401
from client.cart.cart import CartScreen  # noqa: F401
from client.address.address import AddressScreen  # noqa: F401
from client.orders.orders import OrdersScreen  # noqa: F401
from client.wallet.wallet import WalletScreen  # noqa: F401
from client.cards.cards import CardsScreen  # noqa: F401
from client.profile.profile import ProfileScreen  # noqa: F401
from chef.dashboard.dashboard import ChefDashboardScreen  # noqa: F401
from chef.menu.menu import ChefMenuScreen  # noqa: F401
from delivery.dashboard.dashboard import DeliveryDashboardScreen  # noqa: F401
from delivery.orders.orders import DeliveryOrdersScreen  # noqa: F401
from delivery.active.active import DeliveryActiveScreen  # noqa: F401
from delivery.profile.profile import DeliveryProfileScreen  # noqa: F401


class MyApp(App):
    selected_restaurant_id = None
    user_id = None
    user_role = None

    cart = []
    cart_text = StringProperty("Cart")
    cart_qty = 0
    cart_total_price = 0

    cached_addresses = []
    selected_address_id = None
    selected_address_text = None

    selected_payment_method = StringProperty("CASH")
    selected_card_id = None
    selected_card_text = StringProperty("")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.db = DBManager()

    def build(self):
        Builder.load_file("common/theme.kv")
        Builder.load_file("common/login/login.kv")
        Builder.load_file("common/register/register.kv")
        Builder.load_file("client/dashboard/dashboard.kv")
        Builder.load_file("client/restaurant/restaurant.kv")
        Builder.load_file("client/cart/cart.kv")
        Builder.load_file("client/address/address.kv")
        Builder.load_file("client/orders/orders.kv")
        Builder.load_file("client/wallet/wallet.kv")
        Builder.load_file("client/cards/cards.kv")
        Builder.load_file("client/profile/profile.kv")
        Builder.load_file("chef/dashboard/dashboard.kv")
        Builder.load_file("chef/menu/menu.kv")
        Builder.load_file("delivery/dashboard/dashboard.kv")
        Builder.load_file("delivery/orders/orders.kv")
        Builder.load_file("delivery/active/active.kv")
        Builder.load_file("delivery/profile/profile.kv")

        return Builder.load_file("common/root.kv")

    def on_stop(self):
        self.db.close()

    def login(self):
        login_screen = self.root.get_screen("login")
        username = login_screen.ids.username_input.text
        password = login_screen.ids.password_input.text

        cl = self.db.login.check_login(username, password)

        if not cl:
            print("Invalid credentials")
            return

        self.user_id, self.user_role = cl
        self.root.transition = SlideTransition(direction="left")

        if self.user_role == "CHEF":
            self.root.current = "chef_dashboard"
        elif self.user_role == "DELIVERY":
            self.root.current = "delivery_dashboard"
        else:
            self.root.current = "dashboard"

    def open_register_screen(self):
        self.root.transition = SlideTransition(direction="left")
        self.root.current = "register"

    def open_login_screen(self):
        self.root.transition = SlideTransition(direction="right")
        self.root.current = "login"

    def register(self):
        register_screen = self.root.get_screen("register")

        username = register_screen.ids.username_input.text.strip()
        email = register_screen.ids.email_input.text.strip()
        phone = register_screen.ids.phone_input.text.strip()
        password = register_screen.ids.password_input.text
        confirm = register_screen.ids.confirm_input.text

        if not username or not email or not phone or not password:
            register_screen.ids.error_label.text = "Please fill in all fields."
            return

        if not EMAIL_RE.match(email):
            register_screen.ids.error_label.text = "Enter a valid email address."
            return

        if len(password) < 6:
            register_screen.ids.error_label.text = "Password must be at least 6 characters."
            return

        if password != confirm:
            register_screen.ids.error_label.text = "Passwords do not match."
            return

        user_id, error = self.db.login.register(username, password, email, phone)
        if error:
            register_screen.ids.error_label.text = error
            return

        self.user_id = user_id
        self.user_role = "CUSTOMER"
        self.root.transition = SlideTransition(direction="left")
        self.root.current = "dashboard"

    def on_restaurant_press(self, id):
        self.selected_restaurant_id = id
        self.root.transition = SlideTransition(direction="left")
        self.root.current = "restaurant"

    def go_back_to_dashboard(self):
        self.cart = []
        self.cart_text = "Cart"
        self.root.transition = SlideTransition(direction="right")
        self.root.current = "dashboard"

    def logout(self):
        self.root.transition = SlideTransition(direction="right")
        self.user_id = None
        self.root.current = "login"

    def confirm_order(self, order_id):
        restaurant_id = self.db.users.get_restaurant_id(self.user_id)
        self.db.orders.confirm_order(order_id, restaurant_id, self.user_id)
        self.root.get_screen("chef_dashboard").refresh()

    def mark_order_ready(self, order_id):
        restaurant_id = self.db.users.get_restaurant_id(self.user_id)
        self.db.orders.mark_order_ready(order_id, restaurant_id, self.user_id)
        self.root.get_screen("chef_dashboard").refresh()

    def cancel_order_by_chef(self, order_id):
        restaurant_id = self.db.users.get_restaurant_id(self.user_id)
        self.db.orders.cancel_order_by_chef(order_id, restaurant_id, self.user_id)
        self.root.get_screen("chef_dashboard").refresh()

    def open_chef_dashboard(self):
        self.root.transition = SlideTransition(direction="right")
        self.root.current = "chef_dashboard"

    def open_chef_menu_screen(self):
        self.root.transition = SlideTransition(direction="left")
        self.root.current = "chef_menu"

    def confirm_delete_food_item(self, food_id, food_text):
        self._confirm_action(
            "Remove dish",
            f'Remove "{food_text}"?\nThis cannot be undone.',
            lambda: self.delete_food_item(food_id),
            confirm_label="Delete",
        )

    def delete_food_item(self, food_id):
        restaurant_id = self.db.users.get_restaurant_id(self.user_id)
        self.db.restaurants.delete_food_item(food_id, restaurant_id)
        self.root.get_screen("chef_menu").refresh_menu()

    def toggle_food_item_availability(self, food_id):
        restaurant_id = self.db.users.get_restaurant_id(self.user_id)
        self.db.restaurants.toggle_food_availability(food_id, restaurant_id)
        self.root.get_screen("chef_menu").refresh_menu()

    def open_edit_price_popup(self, food_id, current_price):
        content = BoxLayout(orientation="vertical", padding=24, spacing=14)
        with content.canvas.before:
            Color(1, 1, 1, 1)
            card = RoundedRectangle(pos=content.pos, size=content.size, radius=[18])
        content.bind(
            pos=lambda _, value: setattr(card, "pos", value),
            size=lambda _, value: setattr(card, "size", value),
        )

        content.add_widget(Label(
            text="Edit price",
            color=(0.11, 0.11, 0.118, 1),
            bold=True,
            font_size="18sp",
            size_hint_y=None,
            height=28,
        ))

        price_input = TextInput(
            text=f"{current_price:.2f}",
            input_filter="float",
            multiline=False,
            font_size="16sp",
            size_hint_y=None,
            height=48,
            padding=[16, 14, 16, 14],
        )
        content.add_widget(price_input)

        error_label = Label(
            text="",
            color=DANGER,
            bold=True,
            font_size="14sp",
            size_hint_y=None,
            height=20,
        )
        content.add_widget(error_label)

        buttons = BoxLayout(size_hint_y=None, height=50, spacing=12)
        cancel_btn = GhostBtn(text="Cancel")
        save_btn = ActionBtn(text="Save", btn_color=PRIMARY)
        buttons.add_widget(cancel_btn)
        buttons.add_widget(save_btn)
        content.add_widget(buttons)

        popup = Popup(
            title="",
            separator_height=0,
            content=content,
            size_hint=(None, None),
            size=(360, 300),
            auto_dismiss=False,
            background_color=(0, 0, 0, 0),
        )

        def save(*_):
            try:
                price = float(price_input.text.strip())
                if price <= 0:
                    raise ValueError
            except ValueError:
                error_label.text = "Enter a valid price greater than 0."
                return

            restaurant_id = self.db.users.get_restaurant_id(self.user_id)
            success = self.db.restaurants.update_food_price(food_id, restaurant_id, round(price, 2))
            if success:
                popup.dismiss()
                self.root.get_screen("chef_menu").refresh_menu()
            else:
                error_label.text = "Error saving price."

        cancel_btn.bind(on_release=popup.dismiss)
        save_btn.bind(on_release=save)
        popup.open()

    def open_delivery_dashboard(self):
        self.root.transition = SlideTransition(direction="right")
        self.root.current = "delivery_dashboard"

    def open_delivery_restaurant_orders(self, restaurant_id):
        orders_screen = self.root.get_screen("delivery_orders")
        orders_screen.restaurant_id = restaurant_id
        self.root.transition = SlideTransition(direction="left")
        self.root.current = "delivery_orders"

    def open_delivery_active_screen(self):
        self.root.transition = SlideTransition(direction="left")
        self.root.current = "delivery_active"

    def open_delivery_profile_screen(self):
        self.root.transition = SlideTransition(direction="left")
        self.root.current = "delivery_profile"

    def claim_order(self, order_id):
        orders_screen = self.root.get_screen("delivery_orders")
        success = self.db.orders.claim_order_for_delivery(order_id, self.user_id)
        orders_screen.refresh()
        if not success:
            orders_screen.ids.error_label.text = "Someone else already claimed that order."

    def complete_delivery(self, order_id):
        self.db.orders.mark_order_delivered(order_id, self.user_id)
        self.root.get_screen("delivery_active").refresh()

    def confirm_cancel_delivery(self, order_id, order_text):
        self._confirm_action(
            "Cancel delivery",
            f'Cancel "{order_text}"?\nThis cannot be undone.',
            lambda: self.cancel_delivery(order_id),
        )

    def cancel_delivery(self, order_id):
        self.db.orders.cancel_order_by_delivery(order_id, self.user_id)
        self.root.get_screen("delivery_active").refresh()

    def redeem_restaurant_code(self, code_text):
        profile_screen = self.root.get_screen("delivery_profile")

        clean_code = code_text.strip()
        if not clean_code:
            profile_screen.ids.msg_label.color = (0.9, 0.2, 0.2, 1)
            profile_screen.ids.msg_label.text = "Enter a code first."
            return

        restaurant_id, error = self.db.delivery.redeem_invite_code(clean_code, self.user_id)
        if error:
            profile_screen.ids.msg_label.color = (0.9, 0.2, 0.2, 1)
            profile_screen.ids.msg_label.text = error
            return

        profile_screen.ids.code_input.text = ""
        profile_screen.ids.msg_label.color = (0.1, 0.7, 0.3, 1)
        profile_screen.ids.msg_label.text = "Restaurant added!"

    def on_food_press(self, id):
        for item in self.cart:
            if item["id"] == id:
                item["quantity"] += 1
                break
        else:
            self.cart.append({"id": id, "quantity": 1})
        self.cart_qty += 1

        self._sync_cart_badge()

    def increment_cart_item(self, id):
        self.on_food_press(id)
        self._refresh_cart_view()

    def decrement_cart_item(self, id):
        for item in self.cart:
            if item["id"] == id:
                item["quantity"] -= 1
                self.cart_qty -= 1
                if item["quantity"] <= 0:
                    self.cart.remove(item)
                break

        self._sync_cart_badge()
        self._refresh_cart_view()

    def remove_cart_item(self, id):
        for item in self.cart:
            if item["id"] == id:
                self.cart_qty -= item["quantity"]
                self.cart.remove(item)
                break

        self._sync_cart_badge()
        self._refresh_cart_view()

    def _sync_cart_badge(self):
        self.cart_text = f"Cart: {self.cart_qty}" if self.cart_qty else "Cart"

    def _refresh_cart_view(self):
        cart_screen = self.root.get_screen("cart")
        data = self.db.orders.get_cart_items(self.cart)
        total_price = sum(float(item["price"]) for item in data)

        cart_screen.ids.rv.data = data
        self.cart_total_price = total_price
        cart_screen.update_checkout_text()

    def open_cart(self):
        self.root.transition = SlideTransition(direction="up")
        self.root.current = "cart"

    def go_back_to_menu(self):
        self.root.transition = SlideTransition(direction="down")
        self.root.current = "restaurant"

    def open_address_screen(self):
        self.root.get_screen("address").ids.address_input.text = ""
        self.root.get_screen("address").ids.error_label.text = ""
        self.root.transition = SlideTransition(direction="left")
        self.root.current = "address"

    def save_new_address(self, text_content):
        address_screen = self.root.get_screen("address")
        clean_text = text_content.strip()

        if not clean_text:
            address_screen.ids.error_label.text = "Address field cannot be empty!"
            return

        success = self.db.addresses.add_address(self.user_id, clean_text)
        if success:
            address_screen.ids.address_input.text = ""
            address_screen.ids.error_label.text = ""
            address_screen.refresh_addresses()
        else:
            address_screen.ids.error_label.text = "Error saving location profile to database."

    def _confirm_action(self, title, message, on_confirm, confirm_label="Remove"):
        content = BoxLayout(orientation="vertical", padding=24, spacing=14)
        with content.canvas.before:
            Color(1, 1, 1, 1)
            card = RoundedRectangle(pos=content.pos, size=content.size, radius=[18])
        content.bind(
            pos=lambda _, value: setattr(card, "pos", value),
            size=lambda _, value: setattr(card, "size", value),
        )

        content.add_widget(Label(
            text=title,
            color=(0.11, 0.11, 0.118, 1),
            bold=True,
            font_size="18sp",
            size_hint_y=None,
            height=28,
        ))
        content.add_widget(Label(
            text=message,
            color=(0.35, 0.35, 0.37, 1),
            halign="center",
            valign="middle",
            text_size=(312, None),
        ))

        buttons = BoxLayout(size_hint_y=None, height=50, spacing=12)
        cancel_btn = GhostBtn(text="Cancel")
        confirm_btn = ActionBtn(text=confirm_label, btn_color=DANGER)
        buttons.add_widget(cancel_btn)
        buttons.add_widget(confirm_btn)
        content.add_widget(buttons)

        popup = Popup(
            title="",
            separator_height=0,
            content=content,
            size_hint=(None, None),
            size=(360, 240),
            auto_dismiss=False,
            background_color=(0, 0, 0, 0),
        )

        cancel_btn.bind(on_release=popup.dismiss)
        confirm_btn.bind(on_release=lambda *_: (popup.dismiss(), on_confirm()))
        popup.open()

    def _show_alert(self, title, message):
        content = BoxLayout(orientation="vertical", padding=24, spacing=14)
        with content.canvas.before:
            Color(1, 1, 1, 1)
            card = RoundedRectangle(pos=content.pos, size=content.size, radius=[18])
        content.bind(
            pos=lambda _, value: setattr(card, "pos", value),
            size=lambda _, value: setattr(card, "size", value),
        )

        content.add_widget(Label(
            text=title,
            color=DANGER,
            bold=True,
            font_size="18sp",
            size_hint_y=None,
            height=28,
        ))
        content.add_widget(Label(
            text=message,
            color=(0.35, 0.35, 0.37, 1),
            halign="center",
            valign="middle",
            text_size=(312, None),
        ))

        ok_btn = ActionBtn(text="OK", btn_color=DANGER, size_hint_y=None, height=50)
        content.add_widget(ok_btn)

        popup = Popup(
            title="",
            separator_height=0,
            content=content,
            size_hint=(None, None),
            size=(360, 220),
            auto_dismiss=False,
            background_color=(0, 0, 0, 0),
        )
        ok_btn.bind(on_release=popup.dismiss)
        popup.open()

    def confirm_delete_address(self, address_id, address_text):
        self._confirm_action(
            "Remove address",
            f'Remove "{address_text}"?\nThis cannot be undone.',
            lambda: self.delete_address(address_id),
        )

    def delete_address(self, address_id):
        success, error = self.db.addresses.delete_address(self.user_id, address_id)

        if not success:
            self._show_alert("Can't delete address", error or "Error deleting address. Please try again.")
            return

        if self.selected_address_id == address_id:
            self.selected_address_id = None
            self.selected_address_text = None

        self.root.get_screen("address").refresh_addresses()

    def confirm_delete_card(self, card_id, card_text):
        self._confirm_action(
            "Remove card",
            f'Remove "{card_text}"?\nThis cannot be undone.',
            lambda: self.delete_card(card_id),
        )

    def delete_card(self, card_id):
        success = self.db.cards.delete_card(self.user_id, card_id)
        if not success:
            return

        if self.selected_card_id == card_id:
            self.selected_card_id = None
            self.selected_card_text = ""

        self.root.get_screen("cards").refresh_cards()

    def confirm_delete_order(self, order_id, order_text):
        self._confirm_action(
            "Delete order",
            f'Delete "{order_text}"?\nThis cannot be undone.',
            lambda: self.delete_order(order_id),
            confirm_label="Delete",
        )

    def delete_order(self, order_id):
        self.db.orders.cancel_order_by_customer(order_id, self.user_id)
        self.root.get_screen("orders").refresh_orders()

    def on_address_selected(self, chosen_text):
        if chosen_text == "Select Address":
            self.selected_address_id = None
            self.selected_address_text = None
            return

        self.selected_address_text = chosen_text
        for item in self.cached_addresses:
            if item["address"] == chosen_text:
                self.selected_address_id = item["id"]
                break

    def set_payment_method(self, method):
        self.selected_payment_method = method

    def on_card_selected(self, card_id, card_text):
        self.selected_card_id = card_id
        self.selected_card_text = card_text

    def on_checkout(self):
        cart_screen = self.root.get_screen("cart")

        cart_food_ids = [item["id"] for item in self.cart]
        food_items = self.db.restaurants.get_items_by_ids(cart_food_ids)
        unavailable_names = [item["name"] for item in food_items if not item["available"]]

        if unavailable_names:
            for item in food_items:
                if not item["available"]:
                    self.remove_cart_item(item["id"])
            self._show_alert(
                "Items no longer available",
                "These items are no longer available and were removed from your cart: "
                f"{', '.join(unavailable_names)}. Please review your order.",
            )
            return

        if self.selected_address_id is None:
            self._show_alert("Address required", "Please select a delivery address before placing your order.")
            return

        notes = cart_screen.ids.notes_input.text.strip() or None
        tip = cart_screen.get_tip_amount()
        total_with_tip = self.cart_total_price + tip

        if self.selected_payment_method == "CARD":
            if self.selected_card_id is None:
                self._show_alert("Card required", "Please select a card to pay with before placing your order.")
                return

            balance = self.db.wallet.get_balance(self.user_id)

            if balance is None:
                cart_screen.ids.error_label.text = "Error: Wallet not found."
                return

            if balance < total_with_tip:
                cart_screen.ids.error_label.text = f"Insufficient funds! You need {total_with_tip - balance:.2f}€ more."
                return

            order_success = self.db.orders.submit_order(
                self.user_id, self.selected_address_id, self.cart_total_price, "CARD", notes,
                restaurant_id=self.selected_restaurant_id, tip=tip,
            )

            if order_success:
                self.db.wallet.update_balance(self.user_id, balance - total_with_tip)
        else:
            order_success = self.db.orders.submit_order(
                self.user_id, self.selected_address_id, self.cart_total_price, "CASH", notes,
                restaurant_id=self.selected_restaurant_id, tip=tip,
            )

        if not order_success:
            cart_screen.ids.error_label.text = "Checkout Error: Failed processing orders record."
            return

        self.cart = []
        self.cart_qty = 0
        self.cart_text = "Cart"
        self.selected_address_id = None
        self.selected_address_text = None
        self.selected_payment_method = "CASH"
        self.selected_card_id = None
        self.selected_card_text = ""

        self.root.transition = SlideTransition(direction="right")
        self.root.current = "dashboard"

    def clear_cart(self):
        self.cart = []
        self.cart_qty = 0
        self.cart_total_price = 0
        self.cart_text = "Cart"

        cart_screen = self.root.get_screen("cart")
        cart_screen.set_tip_option("NONE")
        cart_screen.ids.rv.data = []
        cart_screen.ids.error_label.text = ""

    def open_orders_screen(self):
        self.root.transition = SlideTransition(direction="left")
        self.root.current = "orders"

    def open_profile_screen(self):
        self.root.transition = SlideTransition(direction="left")
        self.root.current = "profile"

    def go_back_to_profile(self):
        self.root.transition = SlideTransition(direction="right")
        self.root.current = "profile"

    def open_cards_screen(self):
        self.root.transition = SlideTransition(direction="left")
        self.root.current = "cards"

    def save_profile_name(self, name_text):
        profile_screen = self.root.get_screen("profile")
        clean_name = name_text.strip()

        if not clean_name:
            profile_screen.ids.msg_label.color = (0.9, 0.2, 0.2, 1)
            profile_screen.ids.msg_label.text = "Name cannot be empty."
            return

        success = self.db.users.update_name(self.user_id, clean_name)
        if success:
            profile_screen.ids.msg_label.color = (0.1, 0.7, 0.3, 1)
            profile_screen.ids.msg_label.text = "Name updated!"
        else:
            profile_screen.ids.msg_label.color = (0.9, 0.2, 0.2, 1)
            profile_screen.ids.msg_label.text = "Error saving name."

    def show_wallet(self):
        self.root.transition = SlideTransition(direction="left")
        self.root.current = "wallet"

    def add_funds(self, amount_text):
        wallet_screen = self.root.get_screen("wallet")

        try:
            amount = float(amount_text)
            if amount <= 0:
                raise ValueError
        except ValueError:
            wallet_screen.ids.msg_label.color = (0.9, 0.2, 0.2, 1)
            wallet_screen.ids.msg_label.text = "Please enter a valid positive amount."
            return

        current_balance = self.db.wallet.get_balance(self.user_id)
        new_balance = current_balance + amount

        self.db.wallet.update_balance(self.user_id, new_balance)

        wallet_screen.ids.balance_label.text = f"{new_balance:.2f}€"
        wallet_screen.ids.amount_input.text = ""
        wallet_screen.ids.msg_label.color = (0.1, 0.7, 0.3, 1)
        wallet_screen.ids.msg_label.text = f"Successfully added {amount:.2f}€!"


if __name__ == "__main__":
    MyApp().run()
