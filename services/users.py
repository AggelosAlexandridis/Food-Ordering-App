class Users:
    def __init__(self, db):
        self.db = db

    def get_profile(self, user_id):
        row = self.db.users.get_profile_row(user_id)
        if not row:
            return None
        return {"username": row[0], "name": row[1], "email": row[2], "phone_number": row[3]}

    def get_restaurant_id(self, user_id):
        return self.db.users.get_restaurant_id(user_id)

    def update_name(self, user_id, name_text):
        clean_name = name_text.strip()
        if not clean_name:
            return False, "Name cannot be empty."

        success = self.db.users.update_name(user_id, clean_name)
        if not success:
            return False, "Error saving name."
        return True, None
