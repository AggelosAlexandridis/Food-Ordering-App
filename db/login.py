class Login:
    def __init__(self, conn):
        self.conn = conn

    def find_credentials(self, username_or_email):
        with self.conn.cursor() as cur:
            cur.execute(
                "SELECT id, role, password FROM users WHERE username=%s OR email=%s",
                (username_or_email, username_or_email),
            )
            return cur.fetchone()

    def username_exists(self, username):
        with self.conn.cursor() as cur:
            cur.execute("SELECT 1 FROM users WHERE username = %s", (username,))
            return cur.fetchone() is not None

    def email_exists(self, email):
        with self.conn.cursor() as cur:
            cur.execute("SELECT 1 FROM users WHERE email = %s", (email,))
            return cur.fetchone() is not None

    def phone_exists(self, phone_number):
        with self.conn.cursor() as cur:
            cur.execute("SELECT 1 FROM users WHERE phone_number = %s", (phone_number,))
            return cur.fetchone() is not None

    def create_user(self, username, hashed_password, email, phone_number, role="CUSTOMER", restaurant_id=None):
        try:
            with self.conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO users (username, password, email, phone_number, role, restaurant_id)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    """,
                    (username, hashed_password, email, phone_number, role, restaurant_id),
                )
                user_id = cur.lastrowid
                cur.execute(
                    "INSERT INTO wallets (user_id, balance) VALUES (%s, 0)", (user_id,)
                )
            self.conn.commit()
            return user_id
        except Exception as e:
            print(f"Error registering user: {e}")
            self.conn.rollback()
            return None
