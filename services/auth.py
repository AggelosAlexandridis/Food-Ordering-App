import re

from .passwords import hash_password, verify_password

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class Auth:
    def __init__(self, db):
        self.db = db

    def login(self, username, password):
        row = self.db.login.find_credentials(username)
        if not row:
            return None

        user_id, role, stored_password = row
        if not verify_password(password, stored_password):
            return None

        return [user_id, role]

    def register(self, username, password, confirm, email, phone_number):
        username = username.strip()
        email = email.strip()
        phone_number = phone_number.strip()

        if not username or not email or not phone_number or not password:
            return None, "Please fill in all fields."

        if not EMAIL_RE.match(email):
            return None, "Enter a valid email address."

        if len(password) < 6:
            return None, "Password must be at least 6 characters."

        if password != confirm:
            return None, "Passwords do not match."

        if self.db.login.username_exists(username):
            return None, "That username is already taken."

        if self.db.login.email_exists(email):
            return None, "That email is already registered."

        if self.db.login.phone_exists(phone_number):
            return None, "That phone number is already registered."

        user_id = self.db.login.create_user(username, hash_password(password), email, phone_number)
        if user_id is None:
            return None, "Error creating account. Please try again."

        return user_id, None
