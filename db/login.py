from .passwords import hash_password, verify_password


class Login:
    def __init__(self, conn):
        self.conn = conn

    def check_login(self, username, password):
        with self.conn.cursor() as cur:
            cur.execute(
                "SELECT id, role, password FROM users WHERE username=%s OR email=%s",
                (username, username),
            )
            res = cur.fetchone()

        if not res:
            return None

        user_id, role, stored_password = res
        if not verify_password(password, stored_password):
            return None

        return [user_id, role]

    def register(self, username, password, email, phone_number, role="CUSTOMER", restaurant_id=None):
        with self.conn.cursor() as cur:
            cur.execute("SELECT 1 FROM users WHERE username = %s", (username,))
            if cur.fetchone():
                return None, "That username is already taken."

            cur.execute("SELECT 1 FROM users WHERE email = %s", (email,))
            if cur.fetchone():
                return None, "That email is already registered."

            cur.execute("SELECT 1 FROM users WHERE phone_number = %s", (phone_number,))
            if cur.fetchone():
                return None, "That phone number is already registered."

        try:
            with self.conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO users (username, password, email, phone_number, role, restaurant_id)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    """,
                    (username, hash_password(password), email, phone_number, role, restaurant_id),
                )
                user_id = cur.lastrowid
                cur.execute(
                    "INSERT INTO wallets (user_id, balance) VALUES (%s, 0)", (user_id,)
                )
            self.conn.commit()
            return user_id, None
        except Exception as e:
            print(f"Error registering user: {e}")
            self.conn.rollback()
            return None, "Error creating account. Please try again."
