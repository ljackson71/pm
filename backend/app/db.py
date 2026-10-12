import json
import os
import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

DEMO_BOARD = Path(__file__).parent / "demo_board.json"

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY,
    username TEXT NOT NULL UNIQUE,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS boards (
    id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL UNIQUE REFERENCES users(id) ON DELETE CASCADE,
    data TEXT NOT NULL,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
"""


def db_path() -> Path:
    return Path(os.environ.get("DB_PATH", "data/app.db"))


@contextmanager
def connect() -> Iterator[sqlite3.Connection]:
    conn = sqlite3.connect(db_path(), autocommit=True)
    try:
        conn.execute("PRAGMA foreign_keys = ON")
        yield conn
    finally:
        conn.close()


def init_db():
    db_path().parent.mkdir(parents=True, exist_ok=True)
    with connect() as conn:
        conn.executescript(SCHEMA)
        conn.execute("INSERT OR IGNORE INTO users (username) VALUES ('user')")


def get_board(username: str) -> dict:
    with connect() as conn:
        row = conn.execute(
            "SELECT boards.data FROM users LEFT JOIN boards ON boards.user_id = users.id"
            " WHERE users.username = ?",
            (username,),
        ).fetchone()
    if row[0] is None:
        board = json.loads(DEMO_BOARD.read_text())
        save_board(username, board)
        return board
    return json.loads(row[0])


def save_board(username: str, board: dict):
    with connect() as conn:
        conn.execute(
            "INSERT INTO boards (user_id, data) SELECT id, ? FROM users WHERE username = ?"
            " ON CONFLICT (user_id) DO UPDATE SET data = excluded.data,"
            " updated_at = CURRENT_TIMESTAMP",
            (json.dumps(board), username),
        )
