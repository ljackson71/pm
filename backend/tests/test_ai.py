import json
import os
from pathlib import Path
from types import SimpleNamespace

import pytest
from dotenv import load_dotenv
from fastapi.testclient import TestClient

from app import ai, db
from app.main import app

load_dotenv(Path(__file__).parents[2] / ".env")

DEMO_BOARD = json.loads(db.DEMO_BOARD.read_text())


class FakeClient:
    def __init__(self, result: ai.ChatResult):
        self.requests = []
        self.responses = SimpleNamespace(parse=self.parse)
        self.result = result

    def parse(self, **kwargs):
        self.requests.append(kwargs)
        return SimpleNamespace(output_parsed=self.result)


@pytest.fixture
def signed_in():
    with TestClient(app) as client:
        client.post("/api/login", json={"username": "user", "password": "password"})
        yield client


def use_fake(monkeypatch, result: ai.ChatResult) -> FakeClient:
    fake = FakeClient(result)
    monkeypatch.setattr(ai, "client", lambda: fake)
    return fake


def test_reply_only_leaves_board_unchanged(monkeypatch, signed_in):
    use_fake(monkeypatch, ai.ChatResult(reply="You have 8 cards.", board=None))

    response = signed_in.post("/api/chat", json={"message": "How many cards?"})

    assert response.status_code == 200
    assert response.json() == {"reply": "You have 8 cards.", "board": None}
    assert signed_in.get("/api/board").json() == DEMO_BOARD


def test_response_with_board_saves_it(monkeypatch, signed_in):
    board = ai.ChatBoard(
        columns=[ai.ChatColumn(id="col-backlog", title="Backlog")],
        cards=[ai.ChatCard(id="card-x", title="New", details="From AI", column_id="col-backlog")],
    )
    use_fake(monkeypatch, ai.ChatResult(reply="Done.", board=board))

    response = signed_in.post("/api/chat", json={"message": "Replace everything"})

    expected = {
        "columns": [{"id": "col-backlog", "title": "Backlog", "cardIds": ["card-x"]}],
        "cards": {"card-x": {"id": "card-x", "title": "New", "details": "From AI"}},
    }
    assert response.status_code == 200
    assert response.json() == {"reply": "Done.", "board": expected}
    assert signed_in.get("/api/board").json() == expected


def test_invalid_board_from_model_returns_error_and_does_not_save(monkeypatch, signed_in):
    board = ai.ChatBoard(
        columns=[ai.ChatColumn(id="col-backlog", title="Backlog")],
        cards=[ai.ChatCard(id="card-x", title="New", details="", column_id="col-missing")],
    )
    use_fake(monkeypatch, ai.ChatResult(reply="Done.", board=board))

    response = signed_in.post("/api/chat", json={"message": "Break it"})

    assert response.status_code == 502
    assert signed_in.get("/api/board").json() == DEMO_BOARD


def test_request_includes_history_and_board(monkeypatch, signed_in):
    fake = use_fake(monkeypatch, ai.ChatResult(reply="Sure.", board=None))
    history = [
        {"role": "user", "content": "Hi"},
        {"role": "assistant", "content": "Hello!"},
    ]

    signed_in.post("/api/chat", json={"message": "Thanks", "history": history})

    [request] = fake.requests
    assert request["model"] == ai.MODEL
    assert request["text_format"] is ai.ChatResult
    assert request["input"] == [*history, {"role": "user", "content": "Thanks"}]
    board_json = json.loads(request["instructions"].split("Current board:\n")[1])
    assert ai.ChatBoard.model_validate(board_json).to_board().model_dump(by_alias=True) == DEMO_BOARD
    assert board_json["cards"][0] == {**DEMO_BOARD["cards"]["card-1"], "column_id": "col-backlog"}


def test_chat_requires_session():
    assert TestClient(app).post("/api/chat", json={"message": "Hi"}).status_code == 401


def column_titles_of(board: dict, card_title: str) -> list[str]:
    ids = {card["id"] for card in board["cards"].values() if card["title"] == card_title}
    return [column["title"] for column in board["columns"] if ids & set(column["cardIds"])]


@pytest.mark.skipif(not os.environ.get("OPENAI_API_KEY"), reason="OPENAI_API_KEY not set")
def test_live_add_then_move_card(signed_in):
    title = "Write release notes"
    history = []

    for message, column in [
        (f'Add a card called "{title}" to Backlog', "Backlog"),
        (f'Move "{title}" to Done', "Done"),
    ]:
        response = signed_in.post("/api/chat", json={"message": message, "history": history})
        assert response.status_code == 200
        assert column_titles_of(signed_in.get("/api/board").json(), title) == [column]
        history += [
            {"role": "user", "content": message},
            {"role": "assistant", "content": response.json()["reply"]},
        ]
