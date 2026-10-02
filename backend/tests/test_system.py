def test_root(client):
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "LifeOps API is running"}


def test_healthz(client):
    response = client.get("/healthz")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_readyz_checks_database(client):
    response = client.get("/readyz")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "database": "ok"}


def test_readyz_returns_503_when_database_is_down(client):
    from app.database import get_db
    from app.main import app

    class BrokenSession:
        def execute(self, *args, **kwargs):
            raise RuntimeError("connection refused")

    app.dependency_overrides[get_db] = lambda: BrokenSession()
    try:
        response = client.get("/readyz")
    finally:
        app.dependency_overrides.pop(get_db)

    assert response.status_code == 503
    assert response.json()["status"] == "unavailable"


def test_openapi_docs_available(client):
    assert client.get("/docs").status_code == 200
    paths = client.get("/openapi.json").json()["paths"]
    for path in ["/weights", "/money/summary", "/calendar/agenda/today",
                 "/invest/portfolio", "/career/pipeline", "/dashboard"]:
        assert path in paths
