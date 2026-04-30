import pytest

from app import create_app
from app.store import InMemoryStore


class DummyProvider:
    def get_stock_metrics(self, symbol: str):
        ticker = symbol.upper().strip()
        if ticker == "MISS":
            from app.stock_service import StockNotFoundError

            raise StockNotFoundError("Ticker 'MISS' not found")

        return {
            "ticker": ticker,
            "name": "Demo Corp",
            "industry": "TECHNOLOGY",
            "sector": "TECHNOLOGY",
            "pe_ratio": 12.0,
            "growth_rate": 18.0,
            "growth_over_pe": 1.5,
            "growth_over_pe_pass": True,
            "lynch_rule_pass": True,
            "analyst_target_price": 180.0,
            "week_52_high": 190.0,
            "week_52_low": 120.0,
            "description": "Demo description",
        }


@pytest.fixture
def app_instance():
    store = InMemoryStore()
    app = create_app(
        {
            "TESTING": True,
            "SECRET_KEY": "test-secret",
            "STORE": store,
            "POST_SAVE_DELAY_SECONDS": 0,
        }
    )
    app.config["STOCK_PROVIDER"] = DummyProvider()

    yield app


@pytest.fixture
def client(app_instance):
    return app_instance.test_client()
