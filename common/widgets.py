from kivy.properties import BooleanProperty, ListProperty, NumericProperty, StringProperty
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button

PRIMARY = [1, 0.357, 0.235, 1]
DANGER = [0.851, 0.235, 0.235, 1]


class ActionBtn(Button):
    btn_color = ListProperty(PRIMARY)


class GhostBtn(Button):
    line_color = ListProperty(DANGER)


class ListCard(ButtonBehavior, BoxLayout):
    accent = ListProperty(PRIMARY)
    text = StringProperty("")


class OrderListCard(ListCard):
    status = StringProperty("")


class MenuItemCard(ListCard):
    available = BooleanProperty(True)
    price = NumericProperty(0)


class TogglePill(Button):
    selected = BooleanProperty(False)


class ProfileIconBtn(Button):
    pass


class ThemedSpinnerOption(Button):
    """Row widget for a themed Spinner's dropdown list (set via option_cls)."""
    pass
