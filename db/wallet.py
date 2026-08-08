class Wallet:
    def __init__(self, conn):
        self.conn = conn

    def get_balance(self, user_id):
        with self.conn.cursor() as cur:
            cur.execute("SELECT balance FROM wallets WHERE user_id=%s", (user_id,))
            res = cur.fetchone()
        return float(res[0]) if res else None

    def update_balance(self, user_id, new_balance):
        try:
            with self.conn.cursor() as cur:
                cur.execute(
                    "UPDATE wallets SET balance=%s WHERE user_id=%s",
                    (new_balance, user_id),
                )
            self.conn.commit()
            return True
        except Exception as e:
            print(f"Error updating balance: {e}")
            self.conn.rollback()
            return False
