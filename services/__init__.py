from .addresses import Addresses
from .auth import Auth
from .cards import Cards
from .delivery import Delivery
from .orders import Orders
from .restaurants import Restaurants
from .users import Users
from .wallet import Wallet


class ServiceManager:
    def __init__(self, db):
        self.auth = Auth(db)
        self.addresses = Addresses(db)
        self.cards = Cards(db)
        self.delivery = Delivery(db)
        self.orders = Orders(db)
        self.restaurants = Restaurants(db)
        self.users = Users(db)
        self.wallet = Wallet(db)
