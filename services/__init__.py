from .addresses import Addresses
from .auth import Auth
from .cards import Cards
from .delivery import Delivery
from .orders import Orders
from .restaurants import Restaurants
from .users import Users
from .wallet import Wallet


class ServiceManager:
    """Business-logic tier: validation, calculations and orchestration.

    Sits between the Controller (Screens/MyApp) and the Model (DBManager's
    repositories + the relational schema). Screens/Controller should never
    call `app.db.*` directly — always go through `app.services.*`.
    """

    def __init__(self, db):
        self.auth = Auth(db)
        self.addresses = Addresses(db)
        self.cards = Cards(db)
        self.delivery = Delivery(db)
        self.orders = Orders(db)
        self.restaurants = Restaurants(db)
        self.users = Users(db)
        self.wallet = Wallet(db)
