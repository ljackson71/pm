import importlib

from fastapi.testclient import TestClient

import app.main


def test_health():
    client = TestClient(app.main.app)
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_root_serves_static_index(tmp_path, monkeypatch):
    (tmp_path / "index.html").write_text("<h1>Kanban</h1>")
    monkeypatch.setenv("STATIC_DIR", str(tmp_path))
    client = TestClient(importlib.reload(app.main).app)
    response = client.get("/")
    assert response.status_code == 200
    assert "<h1>Kanban</h1>" in response.text
    assert client.get("/api/health").json() == {"status": "ok"}
