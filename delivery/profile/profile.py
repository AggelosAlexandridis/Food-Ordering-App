from kivy.app import App
from kivy.uix.screenmanager import Screen


class DeliveryProfileScreen(Screen):
    def on_enter(self):
        app = App.get_running_app()
        self.ids.code_input.text = ""
        self.ids.msg_label.text = ""

        income = app.db.orders.get_delivery_income(app.user_id)
        self.ids.income_label.text = f"{income['total']:.2f}€"
        self.ids.income_detail.text = (
            f"{income['deliveries']} deliveries · "
            f"{income['flat_fees']:.2f}€ fees + {income['tips']:.2f}€ tips"
        )
