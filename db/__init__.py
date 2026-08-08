from .addresses import Addresses
from .cards import Cards
from .connection import create_connection
from .delivery import Delivery
from .login import Login
from .orders import Orders
from .restaurants import Restaurants
from .users import Users
from .wallet import Wallet


class DBManager:
    def __init__(self):
        self.conn = create_connection()
        self.login = Login(self.conn)
        self.restaurants = Restaurants(self.conn)
        self.wallet = Wallet(self.conn)
        self.addresses = Addresses(self.conn)
        self.orders = Orders(self.conn)
        self.cards = Cards(self.conn)
        self.users = Users(self.conn)
        self.delivery = Delivery(self.conn)

    def close(self):
        if self.conn:
            self.conn.close()
