import mariadb
import os
from dotenv import load_dotenv

load_dotenv()

class DBManager:
    def __init__(self):
        self.conn = mariadb.connect(
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            host=os.getenv("DB_HOST"),
            port=int(os.getenv("DB_PORT")),
            database=os.getenv("DATABASE")
        )

    def close(self):
        if self.conn:
            self.conn.close()

    def check_login(self, username, password):
        cur = self.conn.cursor()
        cur.execute("SELECT id, role FROM users WHERE username=%s AND password=%s", (username, password))
        res = cur.fetchone()
        cur.close()
        return [res[0], res[1]] if res else None

    def get_restaurants(self):
        cur = self.conn.cursor()
        cur.execute("SELECT * FROM restaurants")
        res = cur.fetchall()
        cur.close()
        return [{"id": row[0], "text": row[1]} for row in res]

    def get_menu(self, restaurant_id):
        cur = self.conn.cursor()
        cur.execute("SELECT * FROM food WHERE restaurant_id=%s", (restaurant_id,))
        res = cur.fetchall()
        cur.close()
        return [{"id": row[0], "text": f"{row[1]}: {float(row[2])}€"} for row in res] if isinstance(res, list) else []

    def get_balance(self, user_id):
        cur = self.conn.cursor()
        cur.execute("SELECT balance FROM wallets WHERE user_id=%s", (user_id,))
        res = cur.fetchone()
        cur.close()
        return float(res[0]) if res else None

    def update_balance(self, user_id, new_balance):
        cur = self.conn.cursor()
        try:
            cur.execute("UPDATE wallets SET balance=%s WHERE user_id=%s", (new_balance, user_id))
            self.conn.commit()
            return True
        except Exception as e:
            print(f"Error updating balance: {e}")
            self.conn.rollback()
            return False
        finally:
            cur.close()

    def get_cart_items(self, cart):
        if not cart:
            return []

        cur = self.conn.cursor()
        ids = [item["id"] for item in cart]
        placeholders = ",".join(["%s"] * len(ids))
        query = f"SELECT id, name, price FROM food WHERE id IN ({placeholders})"

        cur.execute(query, ids)
        res = cur.fetchall()
        cur.close()

        quantity_map = {}
        for item in cart:
            quantity_map[item["id"]] = quantity_map.get(item["id"], 0) + item["quantity"]

        result = []
        for row in res:
            food_id = row[0]
            qty = quantity_map.get(food_id, 0)
            result.append({
                "id": food_id,
                "text": f"{row[1]} x{qty}: {float(row[2]) * qty:.1f}€",
                "price": float(f"{float(row[2]) * qty:.1f}")
            })

        return result

    def submit_order(self, user_id, address_id, price):
        cur = self.conn.cursor()
        try:
            cur.execute("SELECT id FROM wallets WHERE user_id = %s LIMIT 1", (user_id,))
            wallet_row = cur.fetchone()
            
            if not wallet_row:
                print(f"Error: No wallet found for user_id {user_id}")
                return False
                
            wallet_id = wallet_row[0]

            cur.execute(
                """
                INSERT INTO orders (user_id, address_id, price, payment_method, wallet_id, status) 
                VALUES (%s, %s, %s, 'CARD', %s, 'PENDING')
                """, 
                (user_id, address_id, price, wallet_id)
            )            
            self.conn.commit()
            return True
        except Exception as e:
            print(f"Error submitting order: {e}")
            self.conn.rollback()
            return False
        finally:
            cur.close()

    def add_address(self, user_id, address_text):
        cur = self.conn.cursor()
        try:
            cur.execute(
                "INSERT INTO addresses (user_id, address) VALUES (%s, %s)", 
                (user_id, address_text)
            )
            self.conn.commit()
            return True
        except Exception as e:
            print(f"Database error adding address: {e}")
            self.conn.rollback()
            return False
        finally:
            cur.close()

    def get_addresses(self, user_id):
        cur = self.conn.cursor()
        cur.execute("SELECT id, address FROM addresses WHERE user_id = %s", (user_id,))
        res = cur.fetchall()
        cur.close()
        return [{"id": row[0], "address": row[1]} for row in res]

    def get_user_orders(self, user_id):
        cur = self.conn.cursor()
        cur.execute(
            """
            SELECT id, price, status, created_at 
            FROM orders 
            WHERE user_id = %s 
            ORDER BY created_at DESC
            """, 
            (user_id,)
        )
        res = cur.fetchall()
        cur.close()

        return [
            {
                "text": f"Order #{row[0]} | Status: {row[2]}\nTotal: {row[1]}€ | Date: {row[3].strftime('%Y-%m-%d %H:%M')}"
            } 
            for row in res
        ]
