class Orders:
    DELIVERY_FLAT_FEE = 2.50

    def __init__(self, conn):
        self.conn = conn

    def get_cart_items(self, cart):
        if not cart:
            return []

        ids = [item["id"] for item in cart]
        placeholders = ",".join(["%s"] * len(ids))

        with self.conn.cursor() as cur:
            cur.execute(
                f"SELECT id, name, price FROM food WHERE id IN ({placeholders})", ids
            )
            res = cur.fetchall()

        quantity_map = {}
        for item in cart:
            quantity_map[item["id"]] = quantity_map.get(item["id"], 0) + item["quantity"]

        result = []
        for food_id, name, price in res:
            qty = quantity_map.get(food_id, 0)
            line_total = float(f"{float(price) * qty:.1f}")
            result.append({
                "id": food_id,
                "text": f"{name} x{qty}: {line_total}€",
                "price": line_total,
            })
        return result

    def submit_order(self, user_id, address_id, price, payment_method, notes=None,
                      restaurant_id=None, tip=0):
        try:
            with self.conn.cursor() as cur:
                wallet_id = None

                if payment_method == "CARD":
                    cur.execute(
                        "SELECT id FROM wallets WHERE user_id = %s LIMIT 1", (user_id,)
                    )
                    wallet_row = cur.fetchone()

                    if not wallet_row:
                        print(f"Error: No wallet found for user_id {user_id}")
                        return False

                    wallet_id = wallet_row[0]

                cur.execute(
                    """
                    INSERT INTO orders
                        (user_id, restaurant_id, address_id, price, tip, notes, payment_method, wallet_id, status)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 'PENDING')
                    """,
                    (user_id, restaurant_id, address_id, price, tip, notes, payment_method, wallet_id),
                )
            self.conn.commit()
            return True
        except Exception as e:
            print(f"Error submitting order: {e}")
            self.conn.rollback()
            return False

    def get_user_orders(self, user_id):
        with self.conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, price, tip, status, created_at
                FROM orders
                WHERE user_id = %s
                ORDER BY created_at DESC
                """,
                (user_id,),
            )
            res = cur.fetchall()

        result = []
        for order_id, price, tip, status, created_at in res:
            total = float(price) + float(tip)
            text = f"Order #{order_id} | Status: {status}\nTotal: {total:.2f}€"
            if tip:
                text += f" (incl. {float(tip):.2f}€ tip)"
            text += f" | Date: {created_at.strftime('%Y-%m-%d %H:%M')}"
            result.append({"id": order_id, "status": status, "text": text})
        return result

    def cancel_order_by_customer(self, order_id, user_id):
        try:
            with self.conn.cursor() as cur:
                cur.execute(
                    "UPDATE orders SET status = 'CANCELLED' WHERE id = %s AND user_id = %s AND status = 'PENDING'",
                    (order_id, user_id),
                )
                updated = cur.rowcount == 1
            if updated:
                self.conn.commit()
            else:
                self.conn.rollback()
            return updated
        except Exception as e:
            print(f"Error cancelling order {order_id}: {e}")
            self.conn.rollback()
            return False

    # --- Chef ---------------------------------------------------------

    def get_restaurant_orders(self, restaurant_id):
        """All orders for a restaurant, newest first — powers the chef dashboard."""
        with self.conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, price, tip, status, created_at, notes
                FROM orders
                WHERE restaurant_id = %s
                ORDER BY created_at DESC
                """,
                (restaurant_id,),
            )
            res = cur.fetchall()

        result = []
        for order_id, price, tip, status, created_at, notes in res:
            text = f"Order #{order_id} · {status}\n{float(price):.2f}€"
            if tip:
                text += f" + {float(tip):.2f}€ tip"
            text += f" · {created_at.strftime('%Y-%m-%d %H:%M')}"
            if notes:
                preview = notes if len(notes) <= 50 else notes[:47] + "..."
                text += f"\nNote: {preview}"
            result.append({"id": order_id, "status": status, "text": text})
        return result

    def confirm_order(self, order_id, restaurant_id, chef_id):
        return self._chef_transition(
            order_id, restaurant_id,
            "UPDATE orders SET status = 'CONFIRMED', chef_id = %s WHERE id = %s AND restaurant_id = %s AND status = 'PENDING'",
            (chef_id, order_id, restaurant_id),
        )

    def mark_order_ready(self, order_id, restaurant_id, chef_id):
        return self._chef_transition(
            order_id, restaurant_id,
            "UPDATE orders SET status = 'READY' WHERE id = %s AND restaurant_id = %s AND status = 'CONFIRMED' AND chef_id = %s",
            (order_id, restaurant_id, chef_id),
        )

    def cancel_order_by_chef(self, order_id, restaurant_id, chef_id):
        return self._chef_transition(
            order_id, restaurant_id,
            """
            UPDATE orders SET status = 'CANCELLED', chef_id = %s
            WHERE id = %s AND restaurant_id = %s AND status IN ('PENDING', 'CONFIRMED')
            """,
            (chef_id, order_id, restaurant_id),
        )

    def _chef_transition(self, order_id, restaurant_id, query, params):
        try:
            with self.conn.cursor() as cur:
                cur.execute(query, params)
                updated = cur.rowcount == 1
            if updated:
                self.conn.commit()
            else:
                self.conn.rollback()
            return updated
        except Exception as e:
            print(f"Error updating order {order_id}: {e}")
            self.conn.rollback()
            return False

    # --- Delivery -------------------------------------------------------

    def get_ready_orders_for_restaurants(self, restaurant_ids):
        """READY orders (not yet claimed) across the given restaurants."""
        if not restaurant_ids:
            return []

        placeholders = ",".join(["%s"] * len(restaurant_ids))
        with self.conn.cursor() as cur:
            cur.execute(
                f"""
                SELECT o.id, o.price, o.restaurant_id, r.name, o.created_at
                FROM orders o
                JOIN restaurants r ON r.id = o.restaurant_id
                WHERE o.restaurant_id IN ({placeholders}) AND o.status = 'READY'
                ORDER BY o.created_at ASC
                """,
                restaurant_ids,
            )
            res = cur.fetchall()

        return [
            {
                "id": row[0],
                "restaurant_id": row[2],
                "text": f"Order #{row[0]} · {row[3]} · {float(row[1]):.2f}€",
            }
            for row in res
        ]

    def claim_order_for_delivery(self, order_id, delivery_user_id):
        """Atomically claim a READY order. False if someone else got there first."""
        try:
            with self.conn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE orders SET status = 'OUT_FOR_DELIVERY', delivery_user_id = %s
                    WHERE id = %s AND status = 'READY' AND delivery_user_id IS NULL
                    """,
                    (delivery_user_id, order_id),
                )
                claimed = cur.rowcount == 1
            if claimed:
                self.conn.commit()
            else:
                self.conn.rollback()
            return claimed
        except Exception as e:
            print(f"Error claiming order {order_id}: {e}")
            self.conn.rollback()
            return False

    def get_delivery_orders(self, delivery_user_id):
        """Orders this delivery person currently has out for delivery."""
        with self.conn.cursor() as cur:
            cur.execute(
                """
                SELECT o.id, o.price, r.name
                FROM orders o
                JOIN restaurants r ON r.id = o.restaurant_id
                WHERE o.delivery_user_id = %s AND o.status = 'OUT_FOR_DELIVERY'
                ORDER BY o.created_at ASC
                """,
                (delivery_user_id,),
            )
            res = cur.fetchall()

        return [
            {"id": row[0], "text": f"Order #{row[0]} · {row[2]} · {float(row[1]):.2f}€"}
            for row in res
        ]

    def mark_order_delivered(self, order_id, delivery_user_id):
        return self._delivery_transition(order_id, delivery_user_id, "DELIVERED")

    def cancel_order_by_delivery(self, order_id, delivery_user_id):
        return self._delivery_transition(order_id, delivery_user_id, "CANCELLED")

    def _delivery_transition(self, order_id, delivery_user_id, new_status):
        try:
            with self.conn.cursor() as cur:
                cur.execute(
                    "UPDATE orders SET status = %s WHERE id = %s AND delivery_user_id = %s",
                    (new_status, order_id, delivery_user_id),
                )
                updated = cur.rowcount == 1
            if updated:
                self.conn.commit()
            else:
                self.conn.rollback()
            return updated
        except Exception as e:
            print(f"Error updating order {order_id}: {e}")
            self.conn.rollback()
            return False

    def get_delivery_income(self, delivery_user_id):
        with self.conn.cursor() as cur:
            cur.execute(
                """
                SELECT COUNT(*), COALESCE(SUM(tip), 0)
                FROM orders
                WHERE delivery_user_id = %s AND status = 'DELIVERED'
                """,
                (delivery_user_id,),
            )
            count, tip_total = cur.fetchone()

        count = count or 0
        tip_total = float(tip_total or 0)
        flat_fees = count * self.DELIVERY_FLAT_FEE
        return {
            "deliveries": count,
            "flat_fees": flat_fees,
            "tips": tip_total,
            "total": flat_fees + tip_total,
        }
