import pytest


@pytest.fixture(autouse=True)
def db_path(tmp_path, monkeypatch):
    path = tmp_path / "data" / "app.db"
    monkeypatch.setenv("DB_PATH", str(path))
    return path
