from fastapi.testclient import TestClient

from app.main import app


def test_login_sets_session_cookie():
    client = TestClient(app)
    response = client.post("/api/login", json={"username": "user", "password": "password"})
    assert response.status_code == 200
    assert response.json() == {"username": "user"}
    assert "session" in response.cookies


def test_bad_credentials_return_401():
    client = TestClient(app)
    response = client.post("/api/login", json={"username": "user", "password": "wrong"})
    assert response.status_code == 401
    assert "session" not in response.cookies


def test_me_before_login_after_login_and_after_logout():
    client = TestClient(app)
    assert client.get("/api/me").status_code == 401

    client.post("/api/login", json={"username": "user", "password": "password"})
    response = client.get("/api/me")
    assert response.status_code == 200
    assert response.json() == {"username": "user"}

    client.post("/api/logout")
    assert client.get("/api/me").status_code == 401
