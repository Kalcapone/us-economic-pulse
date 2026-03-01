"""
Flask-Login UserMixin wrapper around a DB user row.
Kept in a separate module to avoid circular imports.
"""
from flask_login import UserMixin


class User(UserMixin):
    def __init__(self, row):
        self.id = row["id"]
        self.username = row["username"]
        self.email = row["email"]
        self.is_approved = row["is_approved"]
        self.is_admin_user = row["is_admin"]

    def get_id(self):
        return str(self.id)
