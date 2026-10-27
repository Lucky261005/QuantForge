from tests.utils import synthetic_csv


def test_watchlist_crud_flow(client, auth_headers):
    r = client.post("/api/v1/watchlists", json={"name": "Tech Leaders"}, headers=auth_headers)
    assert r.status_code == 201, r.text
    watchlist_id = r.json()["id"]

    r = client.post(f"/api/v1/watchlists/{watchlist_id}/items", json={"symbol": "aapl"}, headers=auth_headers)
    assert r.status_code == 201, r.text
    item_id = r.json()["id"]
    assert r.json()["asset"]["symbol"] == "AAPL"

    # Duplicate add should be rejected.
    r = client.post(f"/api/v1/watchlists/{watchlist_id}/items", json={"symbol": "AAPL"}, headers=auth_headers)
    assert r.status_code == 409

    r = client.get(f"/api/v1/watchlists/{watchlist_id}", headers=auth_headers)
    assert len(r.json()["items"]) == 1

    r = client.delete(f"/api/v1/watchlists/{watchlist_id}/items/{item_id}", headers=auth_headers)
    assert r.status_code == 200

    r = client.delete(f"/api/v1/watchlists/{watchlist_id}", headers=auth_headers)
    assert r.status_code == 200


def test_watchlist_isolated_between_users(client, auth_headers):
    client.post(
        "/api/v1/auth/register",
        json={"email": "second@example.com", "username": "seconduser", "password": "password123"},
    )
    r = client.post("/api/v1/auth/login", json={"email": "second@example.com", "password": "password123"})
    other_headers = {"Authorization": f"Bearer {r.json()['access_token']}"}

    r = client.post("/api/v1/watchlists", json={"name": "Mine"}, headers=auth_headers)
    watchlist_id = r.json()["id"]

    r = client.get(f"/api/v1/watchlists/{watchlist_id}", headers=other_headers)
    assert r.status_code == 403


def test_research_notes_crud(client, auth_headers):
    r = client.post(
        "/api/v1/notes",
        json={"title": "MA cross observations", "content": "Works well in trending regimes.", "tags": ["momentum"]},
        headers=auth_headers,
    )
    assert r.status_code == 201, r.text
    note_id = r.json()["id"]

    r = client.put(f"/api/v1/notes/{note_id}", json={"content": "Updated with more detail."}, headers=auth_headers)
    assert r.status_code == 200
    assert r.json()["content"] == "Updated with more detail."

    r = client.get("/api/v1/notes", headers=auth_headers)
    assert r.status_code == 200
    assert r.json()["total"] == 1

    r = client.delete(f"/api/v1/notes/{note_id}", headers=auth_headers)
    assert r.status_code == 200


def test_portfolio_deposit_buy_sell_flow(client, auth_headers):
    r = client.get("/api/v1/portfolio", headers=auth_headers)
    assert r.status_code == 200
    assert r.json()["cash_balance"] == 100_000.0

    files = {"file": ("AAPL.csv", synthetic_csv(seed=3), "text/csv")}
    client.post("/api/v1/assets/upload?symbol=AAPL", files=files, headers=auth_headers)

    r = client.post(
        "/api/v1/portfolio/transactions", json={"type": "buy", "symbol": "AAPL", "quantity": 10}, headers=auth_headers
    )
    assert r.status_code == 201, r.text
    portfolio = r.json()
    assert portfolio["cash_balance"] < 100_000.0
    assert len(portfolio["holdings"]) == 1
    assert portfolio["holdings"][0]["quantity"] == 10

    r = client.post(
        "/api/v1/portfolio/transactions", json={"type": "sell", "symbol": "AAPL", "quantity": 5}, headers=auth_headers
    )
    assert r.status_code == 201, r.text
    assert r.json()["holdings"][0]["quantity"] == 5

    r = client.post(
        "/api/v1/portfolio/transactions", json={"type": "sell", "symbol": "AAPL", "quantity": 100}, headers=auth_headers
    )
    assert r.status_code == 422  # insufficient shares

    r = client.get("/api/v1/portfolio/transactions", headers=auth_headers)
    assert r.status_code == 200
    assert r.json()["total"] == 2
