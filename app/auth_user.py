from __future__ import annotations

from flask_login import UserMixin
from werkzeug.security import check_password_hash


class AuthUser(UserMixin):
    def __init__(self, user_id: str, username: str, password_hash: str):
        self.id = user_id
        self.username = username
        self.password_hash = password_hash

    @classmethod
    def from_item(cls, item: dict) -> "AuthUser":
        return cls(
            user_id=str(item["user_id"]),
            username=str(item["username"]),
            password_hash=str(item["password_hash"]),
        )

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)
