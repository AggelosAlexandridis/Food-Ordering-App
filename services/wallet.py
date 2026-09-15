class Wallet:
    def __init__(self, db):
        self.db = db

    def get_balance(self, user_id):
        return self.db.wallet.get_balance(user_id)

    def add_funds(self, user_id, amount_text):
        try:
            amount = float(amount_text)
            if amount <= 0:
                raise ValueError
        except ValueError:
            return False, None, None, "Please enter a valid positive amount."

        current_balance = self.db.wallet.get_balance(user_id)
        new_balance = current_balance + amount
        self.db.wallet.update_balance(user_id, new_balance)

        return True, amount, new_balance, None
