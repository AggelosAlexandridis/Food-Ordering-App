from kivy.app import App
from kivy.graphics import Color, Line, RoundedRectangle
from kivy.properties import StringProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.screenmanager import Screen
from kivy.uix.scrollview import ScrollView
from kivy.uix.widget import Widget

from common.bottom_sheet import open_bottom_sheet
from common.widgets import ActionBtn, PRIMARY

CARD_ROW_HEIGHT = 60


def _build_card_row(card, is_selected):
    row = Button(
        text=("✓  " if is_selected else "") + card["text"],
        size_hint_y=None,
        height=CARD_ROW_HEIGHT,
        bold=True,
        font_size="15sp",
        color=(0.11, 0.11, 0.118, 1),
        halign="left",
        valign="middle",
        padding=(18, 0),
        background_normal="",
        background_down="",
        background_color=(0, 0, 0, 0),
    )

    accent = PRIMARY if is_selected else (0.902, 0.902, 0.914, 1)
    with row.canvas.before:
        Color(1, 1, 1, 1)
        bg = RoundedRectangle(pos=row.pos, size=row.size, radius=[16])
        Color(*accent)
        border = Line(rounded_rectangle=(row.x, row.y, row.width, row.height, 16), width=1.4)

    def sync(*_):
        bg.pos = row.pos
        bg.size = row.size
        border.rounded_rectangle = (row.x, row.y, row.width, row.height, 16)
        row.text_size = row.size

    row.bind(pos=sync, size=sync)
    return row


class CartScreen(Screen):
    checkout_text = StringProperty("Checkout")
    selected_tip_option = StringProperty("NONE")

    def on_enter(self):
        app = App.get_running_app()
        cart = app.cart

        self.ids.error_label.text = ""
        self.ids.notes_input.text = ""
        self.selected_tip_option = "NONE"
        self.ids.custom_tip_input.text = ""

        balance = app.db.wallet.get_balance(app.user_id)
        self.ids.balance_btn.text = f"Balance: {balance:.2f}€"

        app.cached_addresses = app.db.addresses.get_addresses(app.user_id)
        address_strings = [item["address"] for item in app.cached_addresses]
        self.ids.address_spinner.values = address_strings

        if app.selected_address_text:
            self.ids.address_spinner.text = app.selected_address_text
        else:
            self.ids.address_spinner.text = "Select Address"

        data = app.db.orders.get_cart_items(cart)
        total_price = sum(float(item["price"]) for item in data)

        self.ids.rv.data = data
        app.cart_total_price = total_price
        self.update_checkout_text()

    def set_tip_option(self, option):
        self.selected_tip_option = option
        if option != "CUSTOM":
            self.ids.custom_tip_input.text = ""
        self.update_checkout_text()

    def get_tip_amount(self):
        app = App.get_running_app()

        if self.selected_tip_option in ("10", "15", "20"):
            return round(app.cart_total_price * (int(self.selected_tip_option) / 100), 2)

        if self.selected_tip_option == "CUSTOM":
            try:
                return max(0.0, float(self.ids.custom_tip_input.text or 0))
            except ValueError:
                return 0.0

        return 0.0

    def update_checkout_text(self):
        app = App.get_running_app()
        total = app.cart_total_price + self.get_tip_amount()
        self.checkout_text = f"Checkout: {total:.2f}€"

    def open_card_picker(self):
        app = App.get_running_app()
        cards = app.db.cards.get_cards(app.user_id)

        def build(panel, close):
            panel.add_widget(Label(
                text="Choose a card",
                bold=True,
                font_size="18sp",
                color=(0.11, 0.11, 0.118, 1),
                size_hint_y=None,
                height=30,
            ))

            if not cards:
                panel.add_widget(Label(
                    text="You don't have any saved cards yet.",
                    color=(0.557, 0.557, 0.584, 1),
                    size_hint_y=None,
                    height=30,
                ))

                def go_add_card(*_):
                    close()
                    app.open_cards_screen()

                add_btn = ActionBtn(text="Add a Card", btn_color=PRIMARY)
                add_btn.bind(on_release=go_add_card)
                panel.add_widget(add_btn)
                panel.add_widget(Widget())
                return

            def select(card, *_):
                app.on_card_selected(card["id"], card["text"])
                close()

            scroll = ScrollView(size_hint=(1, 1))
            card_list = BoxLayout(orientation="vertical", size_hint_y=None, spacing=10)
            card_list.bind(minimum_height=card_list.setter("height"))

            for card in cards:
                row = _build_card_row(card, card["id"] == app.selected_card_id)
                row.bind(on_release=lambda inst, c=card: select(c))
                card_list.add_widget(row)

            scroll.add_widget(card_list)
            panel.add_widget(scroll)

        open_bottom_sheet(self, build)
