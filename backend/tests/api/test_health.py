def test_liveness_check_always_ok(client):
    r = client.get("/api/v1/health")
    assert r.status_code == 200
    assert r.json() == {"message": "ok"}


def test_readiness_check_reports_database_and_redis(client):
    r = client.get("/api/v1/health/ready")
    body = r.json()
    assert "database" in body["checks"]
    assert "redis" in body["checks"]
    # The test DB is always reachable, so readiness must be true regardless of
    # whether a real Redis instance happens to be running in this environment.
    assert body["checks"]["database"]["status"] == "ok"
    assert body["ready"] is True
    assert r.status_code == 200
