import mariadb


class Addresses:
    def __init__(self, conn):
        self.conn = conn

    def get_addresses(self, user_id):
        with self.conn.cursor() as cur:
            cur.execute(
                "SELECT id, address FROM addresses WHERE user_id = %s", (user_id,)
            )
            res = cur.fetchall()
        return [
            {"id": row[0], "address": row[1], "text": row[1]} for row in res
        ]

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

            if not deleted:
                self.conn.rollback()
                return False, "Address not found."

            self.conn.commit()
            return True, None
        except mariadb.IntegrityError:
            self.conn.rollback()
            return False, "This address is used by an existing order and can't be deleted."
        except Exception as e:
            print(f"Database error deleting address: {e}")
            self.conn.rollback()
            return False, "Error deleting address. Please try again."
