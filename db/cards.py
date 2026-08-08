class Cards:
    def __init__(self, conn):
        self.conn = conn

    def get_cards(self, user_id):
        with self.conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, card_number, card_holder_name, expiration_date, type
                FROM cards WHERE user_id = %s
                """,
                (user_id,),
            )
            res = cur.fetchall()

        return [
            {
                "id": row[0],
                "card_number": row[1],
                "card_holder_name": row[2],
                "expiration_date": row[3],
                "type": row[4],
                "text": f"{row[4].title()} •••• {row[1][-4:]}  ·  exp {row[3].strftime('%m/%y')}",
            }
            for row in res
        ]

    def add_card(self, user_id, card_number, cvv, card_holder_name, expiration_date, card_type):
        try:
            with self.conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO cards (user_id, cvv, card_number, card_holder_name, expiration_date, type)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    """,
                    (user_id, cvv, card_number, card_holder_name, expiration_date, card_type),
                )
            self.conn.commit()
            return True
        except Exception as e:
            print(f"Database error adding card: {e}")
            self.conn.rollback()
            return False

    def delete_card(self, user_id, card_id):
        try:
            with self.conn.cursor() as cur:
                cur.execute(
                    "DELETE FROM cards WHERE id = %s AND user_id = %s",
                    (card_id, user_id),
                )
            self.conn.commit()
            return True
        except Exception as e:
            print(f"Database error deleting card: {e}")
            self.conn.rollback()
            return False
