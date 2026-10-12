import os
from pathlib import Path
from types import SimpleNamespace

import pytest
from dotenv import load_dotenv
from fastapi.testclient import TestClient

from app import ai
from app.main import app

load_dotenv(Path(__file__).parents[2] / ".env")


class FakeClient:
    def __init__(self, reply: str):
        self.requests = []
        self.chat = SimpleNamespace(completions=SimpleNamespace(create=self.create))
        self.reply = reply

    def create(self, **kwargs):
        self.requests.append(kwargs)
        message = SimpleNamespace(content=self.reply)
        return SimpleNamespace(choices=[SimpleNamespace(message=message)])


def test_ai_test_route_returns_mocked_reply(monkeypatch):
    fake = FakeClient("2 + 2 = 4")
    monkeypatch.setattr(ai, "client", lambda: fake)
    client = TestClient(app)
    client.post("/api/login", json={"username": "user", "password": "password"})

    response = client.post("/api/ai/test")

    assert response.status_code == 200
    assert response.json() == {"reply": "2 + 2 = 4"}
    assert fake.requests == [
        {"model": ai.MODEL, "messages": [{"role": "user", "content": "What is 2+2?"}]}
    ]


def test_ai_test_route_requires_session():
    assert TestClient(app).post("/api/ai/test").status_code == 401


@pytest.mark.skipif(not os.environ.get("OPENAI_API_KEY"), reason="OPENAI_API_KEY not set")
def test_live_openai():
    assert "4" in ai.ask("What is 2+2?")
