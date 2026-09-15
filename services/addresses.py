import mariadb


class Addresses:
    def __init__(self, db):
        self.db = db

    def list_addresses(self, user_id):
        rows = self.db.addresses.get_addresses(user_id)
        return [{"id": row[0], "address": row[1], "text": row[1]} for row in rows]

    def add_address(self, user_id, address_text):
        clean_text = address_text.strip()
        if not clean_text:
            return False, "Address field cannot be empty!"

        success = self.db.addresses.add_address(user_id, clean_text)
        if not success:
            return False, "Error saving location profile to database."
        return True, None

    def delete_address(self, user_id, address_id):
        try:
            deleted = self.db.addresses.delete_address(user_id, address_id)
        except mariadb.IntegrityError:
            return False, "This address is used by an existing order and can't be deleted."

        if not deleted:
            return False, "Address not found."
        return True, None
