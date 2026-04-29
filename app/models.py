from datetime import datetime

from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

from . import db, login_manager


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    favorites = db.relationship("Favorite", backref="user", lazy=True, cascade="all, delete")

    def set_password(self, password: str) -> None:
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)


@login_manager.user_loader
def load_user(user_id: str):
    return User.query.get(int(user_id))


class Favorite(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    ticker = db.Column(db.String(10), nullable=False)
    name = db.Column(db.String(255), nullable=True)
    industry = db.Column(db.String(255), nullable=True)
    pe_ratio = db.Column(db.Float, nullable=True)
    growth_rate = db.Column(db.Float, nullable=True)
    growth_over_pe = db.Column(db.Float, nullable=True)
    analyst_target_price = db.Column(db.Float, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (
        db.UniqueConstraint("user_id", "ticker", name="unique_user_ticker"),
    )

    def to_dict(self) -> dict:
        return {
            "ticker": self.ticker,
            "name": self.name,
            "industry": self.industry,
            "pe_ratio": self.pe_ratio,
            "growth_rate": self.growth_rate,
            "growth_over_pe": self.growth_over_pe,
            "analyst_target_price": self.analyst_target_price,
            "created_at": self.created_at.isoformat(),
        }
