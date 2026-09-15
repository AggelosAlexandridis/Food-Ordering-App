DELIVERY_FLAT_FEE = 2.50


class Orders:
    def __init__(self, db):
        self.db = db

    def get_cart_items(self, cart):
        if not cart:
            return []

        quantity_map = {}
        for item in cart:
            quantity_map[item["id"]] = quantity_map.get(item["id"], 0) + item["quantity"]

        rows = self.db.orders.get_food_prices(list(quantity_map.keys()))

        result = []
        for food_id, name, price in rows:
            qty = quantity_map.get(food_id, 0)
            line_total = float(f"{float(price) * qty:.1f}")
            result.append({
                "id": food_id,
                "text": f"{name} x{qty}: {line_total}€",
                "price": line_total,
            })
        return result

    def checkout(self, user_id, restaurant_id, address_id, payment_method, price, tip, notes):
        total = price + tip

        if payment_method == "CARD":
            balance = self.db.wallet.get_balance(user_id)
            if balance is None:
                return False, "Error: Wallet not found."

            if balance < total:
                return False, f"Insufficient funds! You need {total - balance:.2f}€ more."

            wallet_id = self.db.wallet.get_wallet_id(user_id)
            success = self.db.orders.insert_order(
                user_id, address_id, price, "CARD", notes,
                restaurant_id=restaurant_id, tip=tip, wallet_id=wallet_id,
            )
            if not success:
                return False, "Checkout Error: Failed processing orders record."

            self.db.wallet.update_balance(user_id, balance - total)
            return True, None

        success = self.db.orders.insert_order(
            user_id, address_id, price, "CASH", notes,
            restaurant_id=restaurant_id, tip=tip,
        )
        if not success:
            return False, "Checkout Error: Failed processing orders record."
        return True, None

    def list_user_orders(self, user_id):
        rows = self.db.orders.get_user_orders(user_id)

        result = []
        for order_id, price, tip, status, created_at in rows:
            total = float(price) + float(tip)
            text = f"Order #{order_id} | Status: {status}\nTotal: {total:.2f}€"
            if tip:
                text += f" (incl. {float(tip):.2f}€ tip)"
            text += f" | Date: {created_at.strftime('%Y-%m-%d %H:%M')}"
            result.append({"id": order_id, "status": status, "text": text})
        return result

    def cancel_order(self, order_id, user_id):
        return self.db.orders.cancel_order_by_customer(order_id, user_id)

    def list_restaurant_orders(self, restaurant_id):
        rows = self.db.orders.get_restaurant_orders(restaurant_id)

        result = []
        for order_id, price, tip, status, created_at, notes in rows:
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
        return self.db.orders.confirm_order(order_id, restaurant_id, chef_id)

    def mark_order_ready(self, order_id, restaurant_id, chef_id):
        return self.db.orders.mark_order_ready(order_id, restaurant_id, chef_id)

    def cancel_order_by_chef(self, order_id, restaurant_id, chef_id):
        return self.db.orders.cancel_order_by_chef(order_id, restaurant_id, chef_id)

    def list_ready_orders(self, restaurant_ids):
        rows = self.db.orders.get_ready_orders_for_restaurants(restaurant_ids)
        return [
            {
                "id": row[0],
                "restaurant_id": row[2],
                "text": f"Order #{row[0]} · {row[3]} · {float(row[1]):.2f}€",
            }
            for row in rows
        ]

    def claim_order(self, order_id, delivery_user_id):
        return self.db.orders.claim_order_for_delivery(order_id, delivery_user_id)

    def list_active_deliveries(self, delivery_user_id):
        rows = self.db.orders.get_delivery_orders(delivery_user_id)
        return [
            {"id": row[0], "text": f"Order #{row[0]} · {row[2]} · {float(row[1]):.2f}€"}
            for row in rows
        ]

    def complete_delivery(self, order_id, delivery_user_id):
        return self.db.orders.mark_order_delivered(order_id, delivery_user_id)

    def cancel_delivery(self, order_id, delivery_user_id):
        return self.db.orders.cancel_order_by_delivery(order_id, delivery_user_id)

    def get_delivery_income(self, delivery_user_id):
        count, tip_total = self.db.orders.get_delivery_income_raw(delivery_user_id)
        flat_fees = count * DELIVERY_FLAT_FEE
        return {
            "deliveries": count,
            "flat_fees": flat_fees,
            "tips": tip_total,
            "total": flat_fees + tip_total,
        }
