from flask import Flask
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy

from .config import Config
from .stock_service import AlphaVantageStockProvider

db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = "login_page"


def create_app(test_config: dict | None = None) -> Flask:
    app = Flask(__name__)
    app.config.from_object(Config)

    if test_config:
        app.config.update(test_config)

    db.init_app(app)
    login_manager.init_app(app)

    provider = AlphaVantageStockProvider(app.config["ALPHAVANTAGE_API_KEY"])
    app.config["STOCK_PROVIDER"] = provider

    from .routes import register_routes

    register_routes(app)

    with app.app_context():
        db.create_all()

    return app
