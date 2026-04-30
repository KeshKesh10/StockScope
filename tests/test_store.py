from __future__ import annotations

from app.store import DynamoDBStore


class FakeTable:
    def __init__(self, items=None):
        self.items = items or []
        self.last_query_kwargs = None

    def query(self, **kwargs):
        self.last_query_kwargs = kwargs
        return {"Items": list(self.items)}

    def scan(self):
        return {"Items": list(self.items)}

    def put_item(self, **kwargs):
        self.items.append(kwargs["Item"])

    def get_item(self, **kwargs):
        key = kwargs.get("Key", {})
        for item in self.items:
            if all(item.get(k) == v for k, v in key.items()):
                return {"Item": item}
        return {}

    def delete_item(self, **kwargs):
        key = kwargs.get("Key", {})
        self.items = [
            item for item in self.items if not all(item.get(k) == v for k, v in key.items())
        ]


class FakeDynamoResource:
    def __init__(self):
        self.tables = {
            "users": FakeTable(),
            "favorites": FakeTable(),
            "signups": FakeTable(),
        }

    def Table(self, name):
        return self.tables[name]


def test_list_favorites_uses_gsi_when_industry_filter_provided():
    resource = FakeDynamoResource()
    store = DynamoDBStore(resource, "users", "favorites", "signups")
    store.list_favorites("user-1", "tech")
    kwargs = resource.tables["favorites"].last_query_kwargs
    assert kwargs["IndexName"] == "user-industry-index"


def test_list_signups_uses_category_index_when_filter_present():
    resource = FakeDynamoResource()
    store = DynamoDBStore(resource, "users", "favorites", "signups")
    store.list_signups("colors")
    kwargs = resource.tables["signups"].last_query_kwargs
    assert kwargs["IndexName"] == "category-index"


def test_create_and_read_signup_normalizes_category():
    resource = FakeDynamoResource()
    store = DynamoDBStore(resource, "users", "favorites", "signups")
    store.create_signup(
        {
            "name": "Morgan",
            "email": "morgan@example.com",
            "phone": "5551234567",
            "category": "football",
        }
    )

    rows = store.list_signups("football")
    assert len(rows) == 1
    assert rows[0]["email"] == "morgan@example.com"
