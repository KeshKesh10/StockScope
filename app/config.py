import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-change-me")
    AWS_REGION = os.environ.get("AWS_REGION", "us-east-1")
    DYNAMODB_ENDPOINT_URL = os.environ.get("DYNAMODB_ENDPOINT_URL", "http://localhost:8000")
    AWS_ACCESS_KEY_ID = os.environ.get("AWS_ACCESS_KEY_ID", "local")
    AWS_SECRET_ACCESS_KEY = os.environ.get("AWS_SECRET_ACCESS_KEY", "local")
    USERS_TABLE = os.environ.get("USERS_TABLE", "stockscope-users")
    FAVORITES_TABLE = os.environ.get("FAVORITES_TABLE", "stockscope-favorites")
    SIGNUPS_TABLE = os.environ.get("SIGNUPS_TABLE", "stockscope-signups")
    POST_SAVE_DELAY_SECONDS = int(os.environ.get("POST_SAVE_DELAY_SECONDS", "5"))
    STOCK_DATA_PROVIDER = os.environ.get("STOCK_DATA_PROVIDER", "alpha")
    ALPHAVANTAGE_API_KEY = os.environ.get("ALPHAVANTAGE_API_KEY", "demo")
    FINNHUB_API_KEY = os.environ.get("FINNHUB_API_KEY", "")
