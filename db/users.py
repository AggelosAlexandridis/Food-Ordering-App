class Users:
    def __init__(self, conn):
        self.conn = conn

    def get_profile_row(self, user_id):
        with self.conn.cursor() as cur:
            cur.execute(
                "SELECT username, name, email, phone_number FROM users WHERE id = %s",
                (user_id,),
            )
            return cur.fetchone()

    def get_restaurant_id(self, user_id):
        with self.conn.cursor() as cur:
            cur.execute("SELECT restaurant_id FROM users WHERE id = %s", (user_id,))
            row = cur.fetchone()
        return row[0] if row else None

    def update_name(self, user_id, name):
        try:
            with self.conn.cursor() as cur:
                cur.execute("UPDATE users SET name = %s WHERE id = %s", (name, user_id))
            self.conn.commit()
            return True
        except Exception as e:
            print(f"Database error updating name: {e}")
            self.conn.rollback()
            return False
