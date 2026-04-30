import boto3
from flask import Flask
from flask import current_app
from flask_login import LoginManager

from .auth_user import AuthUser
from .config import Config
from .store import DynamoDBStore, InMemoryStore
from .stock_service import (
    AlphaVantageStockProvider,
    FallbackStockProvider,
    FinnhubStockProvider,
    YFinanceStockProvider,
)

login_manager = LoginManager()
login_manager.login_view = "login_page"


@login_manager.user_loader
def load_user(user_id: str):
    store = current_app.config.get("STORE")
    if not store:
        return None

    item = store.get_user_by_id(user_id)
    if not item:
        return None
    return AuthUser.from_item(item)


def _build_store(app: Flask):
    if app.config.get("TESTING"):
        return app.config.get("STORE") or InMemoryStore()

    dynamodb = boto3.resource(
        "dynamodb",
        region_name=app.config["AWS_REGION"],
        endpoint_url=app.config["DYNAMODB_ENDPOINT_URL"],
        aws_access_key_id=app.config["AWS_ACCESS_KEY_ID"],
        aws_secret_access_key=app.config["AWS_SECRET_ACCESS_KEY"],
    )
    return DynamoDBStore(
        dynamodb_resource=dynamodb,
        users_table=app.config["USERS_TABLE"],
        favorites_table=app.config["FAVORITES_TABLE"],
        signups_table=app.config["SIGNUPS_TABLE"],
    )


def create_app(test_config: dict | None = None) -> Flask:
    app = Flask(__name__)
    app.config.from_object(Config)

    if test_config:
        app.config.update(test_config)

    login_manager.init_app(app)

    provider_name = str(app.config.get("STOCK_DATA_PROVIDER", "alpha")).lower()
    if provider_name == "yfinance":
        provider = YFinanceStockProvider()
    elif provider_name == "finnhub":
        provider = FallbackStockProvider(
            FinnhubStockProvider(app.config["FINNHUB_API_KEY"]),
            YFinanceStockProvider(),
        )
    else:
        provider = FallbackStockProvider(
            AlphaVantageStockProvider(app.config["ALPHAVANTAGE_API_KEY"]),
            YFinanceStockProvider(),
        )
    app.config["STOCK_PROVIDER"] = provider
    app.config["STORE"] = _build_store(app)

    from .routes import register_routes

    register_routes(app)

    return app
