from kivy.app import App
from kivy.lang import Builder
from kivy.properties import StringProperty
from kivy.uix.screenmanager import Screen, SlideTransition
from db import DBManager


class LoginScreen(Screen):
    pass

class DashboardScreen(Screen):
    def on_enter(self):
        app = App.get_running_app()
        self.ids.rv.data = app.db.get_restaurants()

        balance = app.db.get_balance(app.user_id)
        self.ids.balance_btn.text = f"Balance: {balance:.2f}€"

class AddressScreen(Screen):
    pass

class OrdersScreen(Screen):
    def on_enter(self):
        app = App.get_running_app()
        self.ids.rv.data = app.db.get_user_orders(app.user_id)

class WalletScreen(Screen):
    def on_enter(self):
        app = App.get_running_app()
        balance = app.db.get_balance(app.user_id)
        
        self.ids.balance_label.text = f"{balance:.2f}€"
        self.ids.amount_input.text = ""
        self.ids.msg_label.text = ""

class RestaurantScreen(Screen):
    def on_enter(self):
        app = App.get_running_app()
        self.ids.rv.data = app.db.get_menu(app.user_id)


class CartScreen(Screen):
    checkout_text = StringProperty("Checkout")

    def on_enter(self):
        app = App.get_running_app()
        cart = app.cart
        
        self.ids.error_label.text = ""
        
        balance = app.db.get_balance(app.user_id)
        self.ids.balance_btn.text = f"Balance: {balance:.2f}€"
        
        app.cached_addresses = app.db.get_addresses(app.user_id)
        address_strings = [item["address"] for item in app.cached_addresses]
        self.ids.address_spinner.values = address_strings
        
        if app.selected_address_text:
            self.ids.address_spinner.text = app.selected_address_text
        else:
            self.ids.address_spinner.text = "Select Address"

        data = app.db.get_cart_items(cart)
        total_price = sum(float(item['price']) for item in data)

        self.checkout_text = f"Checkout: {total_price:.2f}€"
        self.ids.rv.data = data
        app.cart_total_price = total_price


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

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.db = DBManager()

    def build(self):
        Builder.load_file("screens/login.kv")
        Builder.load_file("screens/dashboard.kv")
        Builder.load_file("screens/restaurant.kv")
        Builder.load_file("screens/cart.kv")
        Builder.load_file("screens/address.kv")
        Builder.load_file("screens/orders.kv")
        Builder.load_file("screens/wallet.kv")

        return Builder.load_file("screens/root.kv")

    def on_stop(self):
        self.db.close()

    def login(self):
        loginScreen = self.root.get_screen("login")
        username = loginScreen.ids.username_input.text
        password = loginScreen.ids.password_input.text

        cl = self.db.check_login(username, password)
        
        if cl:
            self.user_id = cl[0]
            self.user_role = cl[1]
            self.root.transition = SlideTransition(direction="left")
            self.root.current = 'dashboard'
        else:
            print("Invalid credentials")

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

    def on_food_press(self, id):
        for item in self.cart:
            if item["id"] == id:
                item["quantity"] += 1
                break
        else:
            self.cart.append({"id": id, "quantity": 1})
        self.cart_qty += 1

        self.cart_text = f"Cart: {self.cart_qty}"

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
            
        success = self.db.add_address(self.user_id, clean_text)
        if success:
            self.go_back_to_dashboard()
        else:
            address_screen.ids.error_label.text = "Error saving location profile to database."

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

    def on_checkout(self):
        cart_screen = self.root.get_screen("cart")
        
        if self.selected_address_id is None:
            cart_screen.ids.error_label.text = "Please select a delivery address profile!"
            return

        balance = self.db.get_balance(self.user_id)

        if balance is None:
            cart_screen.ids.error_label.text = "Error: Wallet not found."
            return 

        if balance < self.cart_total_price:
            cart_screen.ids.error_label.text = f"Insufficient funds! You need {self.cart_total_price - balance:.2f}€ more."
            return

        order_success = self.db.submit_order(self.user_id, self.selected_address_id, self.cart_total_price)
        
        if not order_success:
            cart_screen.ids.error_label.text = "Checkout Error: Failed processing orders record."
            return

        new_balance = balance - self.cart_total_price
        self.db.update_balance(self.user_id, new_balance)

        self.cart = []
        self.cart_qty = 0
        self.cart_text = "Cart"
        self.selected_address_id = None
        self.selected_address_text = None
        
        self.root.transition = SlideTransition(direction="right")
        self.root.current = "dashboard"

    def clear_cart(self):
        self.cart = []
        self.cart_qty = 0
        self.cart_total_price = 0
        self.cart_text = "Cart"

        cart_screen = self.root.get_screen("cart")
        cart_screen.checkout_text = "Checkout"
        cart_screen.ids.rv.data = []
        cart_screen.ids.error_label.text = ""

    def open_orders_screen(self):
        self.root.transition = SlideTransition(direction="left")
        self.root.current = "orders"

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

        current_balance = self.db.get_balance(self.user_id)
        new_balance = current_balance + amount
        
        self.db.update_balance(self.user_id, new_balance)

        wallet_screen.ids.balance_label.text = f"{new_balance:.2f}€"
        wallet_screen.ids.amount_input.text = ""
        wallet_screen.ids.msg_label.color = (0.1, 0.7, 0.3, 1) # Green text
        wallet_screen.ids.msg_label.text = f"Successfully added {amount:.2f}€!"


if __name__ == "__main__":
    MyApp().run()