import json
import sqlite3

import pytest
from fastapi.testclient import TestClient

from app import db
from app.main import app

BOARD = {
    "columns": [
        {"id": "col-a", "title": "Todo", "cardIds": ["card-1"]},
        {"id": "col-b", "title": "Done", "cardIds": []},
    ],
    "cards": {"card-1": {"id": "card-1", "title": "Write tests", "details": "pytest"}},
}


@pytest.fixture
def client():
    with TestClient(app) as client:
        yield client


@pytest.fixture
def signed_in(client):
    client.post("/api/login", json={"username": "user", "password": "password"})
    return client


def test_db_and_tables_created_when_missing(db_path, client):
    assert db_path.exists()
    with sqlite3.connect(db_path) as conn:
        tables = {row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type = 'table'")}
        users = conn.execute("SELECT username FROM users").fetchall()
    assert {"users", "boards"} <= tables
    assert users == [("user",)]


def test_get_returns_seeded_board(signed_in):
    response = signed_in.get("/api/board")
    assert response.status_code == 200
    board = response.json()
    assert board == json.loads(db.DEMO_BOARD.read_text())
    assert len(board["columns"]) == 5
    assert len(board["cards"]) == 8


def test_put_then_get_round_trips(signed_in):
    response = signed_in.put("/api/board", json=BOARD)
    assert response.status_code == 200
    assert response.json() == BOARD
    assert signed_in.get("/api/board").json() == BOARD


@pytest.mark.parametrize(
    "board",
    [
        {"columns": "nope", "cards": {}},
        {"columns": [{"id": "col-a", "title": "Todo"}], "cards": {}},
        {"columns": [{"id": "col-a", "title": "Todo", "cardIds": ["card-x"]}], "cards": {}},
    ],
    ids=["bad-columns", "missing-card-ids", "dangling-card-id"],
)
def test_put_invalid_board_returns_422(signed_in, board):
    assert signed_in.put("/api/board", json=board).status_code == 422


def test_routes_require_session(client):
    assert client.get("/api/board").status_code == 401
    assert client.put("/api/board", json=BOARD).status_code == 401


def test_users_have_independent_boards(signed_in):
    with db.connect() as conn:
        conn.execute("INSERT INTO users (username) VALUES ('other')")
    db.save_board("other", BOARD)

    assert signed_in.get("/api/board").json() == json.loads(db.DEMO_BOARD.read_text())
    assert db.get_board("other") == BOARD
