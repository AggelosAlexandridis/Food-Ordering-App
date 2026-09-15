import mariadb


class Addresses:
    def __init__(self, conn):
        self.conn = conn

    def get_addresses(self, user_id):
        with self.conn.cursor() as cur:
            cur.execute(
                "SELECT id, address FROM addresses WHERE user_id = %s", (user_id,)
            )
            return cur.fetchall()

    def add_address(self, user_id, address_text):
        try:
            with self.conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO addresses (user_id, address) VALUES (%s, %s)",
                    (user_id, address_text),
                )
            self.conn.commit()
            return True
        except Exception as e:
            print(f"Database error adding address: {e}")
            self.conn.rollback()
            return False

    def delete_address(self, user_id, address_id):
        try:
            with self.conn.cursor() as cur:
                cur.execute(
                    "DELETE FROM addresses WHERE id = %s AND user_id = %s",
                    (address_id, user_id),
                )
                deleted = cur.rowcount == 1

            if deleted:
                self.conn.commit()
            else:
                self.conn.rollback()
            return deleted
        except mariadb.IntegrityError:
            self.conn.rollback()
            raise
        except Exception as e:
            print(f"Database error deleting address: {e}")
            self.conn.rollback()
            return False
