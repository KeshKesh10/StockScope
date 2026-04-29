from app.models import Favorite


def register_and_login(client, username="alice", password="pass1234"):
    client.post("/register", data={"username": username, "password": password})
    return client.post("/login", data={"username": username, "password": password})


def test_stock_api_success(client):
    response = client.post("/api/stock", json={"ticker": "ibm"})
    assert response.status_code == 200
    data = response.get_json()
    assert data["ticker"] == "IBM"
    assert data["growth_over_pe"] == 1.5


def test_stock_api_not_found(client):
    response = client.post("/api/stock", json={"ticker": "MISS"})
    assert response.status_code == 404


def test_favorites_requires_login(client):
    response = client.get("/favorites")
    assert response.status_code == 302
    assert "/login" in response.headers["Location"]


def test_industry_requires_login(client):
    response = client.get("/industry")
    assert response.status_code == 302
    assert "/login" in response.headers["Location"]


def test_profile_requires_login(client):
    response = client.get("/profile")
    assert response.status_code == 302
    assert "/login" in response.headers["Location"]


def test_stock_results_screen_loads(client):
    response = client.get("/stock/ibm")
    assert response.status_code == 200
    assert b"detail-panel" in response.data


def test_favorites_are_per_user(client, app_instance):
    register_and_login(client, "alice", "pass1234")

    add = client.post(
        "/api/favorites",
        json={
            "ticker": "IBM",
            "name": "IBM",
            "industry": "TECH",
            "pe_ratio": 10,
            "growth_rate": 20,
            "growth_over_pe": 2,
            "analyst_target_price": 200,
        },
    )
    assert add.status_code == 201

    listed = client.get("/api/favorites")
    assert listed.status_code == 200
    assert len(listed.get_json()) == 1

    client.post("/logout")
    register_and_login(client, "bob", "pass1234")

    listed_bob = client.get("/api/favorites")
    assert listed_bob.status_code == 200
    assert listed_bob.get_json() == []

    with app_instance.app_context():
        assert Favorite.query.count() == 1


def test_filter_favorites_by_industry(client):
    register_and_login(client, "chris", "pass1234")

    client.post(
        "/api/favorites",
        json={
            "ticker": "IBM",
            "industry": "TECHNOLOGY",
            "pe_ratio": 12,
            "growth_rate": 18,
            "growth_over_pe": 1.5,
        },
    )
    client.post(
        "/api/favorites",
        json={
            "ticker": "PFE",
            "industry": "HEALTHCARE",
            "pe_ratio": 8,
            "growth_rate": 10,
            "growth_over_pe": 1.25,
        },
    )

    response = client.get("/api/favorites?industry=tech")
    assert response.status_code == 200
    payload = response.get_json()
    assert len(payload) == 1
    assert payload[0]["ticker"] == "IBM"
