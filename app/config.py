import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-change-me")
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL", f"sqlite:///{BASE_DIR / 'stockscope.db'}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    ALPHAVANTAGE_API_KEY = os.environ.get("ALPHAVANTAGE_API_KEY", "demo")
