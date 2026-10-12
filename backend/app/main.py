import os
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from starlette.middleware.sessions import SessionMiddleware

from app import ai, db
from app.models import Board, ChatRequest

STATIC_DIR = Path(os.environ.get("STATIC_DIR", Path(__file__).parent / "static"))
SESSION_SECRET = os.environ.get("SESSION_SECRET", "dev-secret")


@asynccontextmanager
async def lifespan(app: FastAPI):
    db.init_db()
    yield


app = FastAPI(lifespan=lifespan)
app.add_middleware(SessionMiddleware, secret_key=SESSION_SECRET)


class Credentials(BaseModel):
    username: str
    password: str


def current_user(request: Request) -> str:
    username = request.session.get("username")
    if username is None:
        raise HTTPException(status_code=401, detail="Not signed in")
    return username


CurrentUser = Annotated[str, Depends(current_user)]


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.post("/api/login")
def login(credentials: Credentials, request: Request):
    if credentials.username != "user" or credentials.password != "password":
        raise HTTPException(status_code=401, detail="Invalid username or password")
    request.session["username"] = credentials.username
    return {"username": credentials.username}


@app.post("/api/logout")
def logout(request: Request):
    request.session.clear()
    return {"status": "ok"}


@app.get("/api/me")
def me(username: CurrentUser):
    return {"username": username}


@app.get("/api/board")
def get_board(username: CurrentUser):
    return db.get_board(username)


@app.put("/api/board")
def put_board(board: Board, username: CurrentUser):
    data = board.model_dump(by_alias=True)
    db.save_board(username, data)
    return data


@app.post("/api/chat")
def chat(request: ChatRequest, username: CurrentUser):
    board = Board.model_validate(db.get_board(username))
    result = ai.chat(board, request.history, request.message)
    if result.board is None:
        return {"reply": result.reply, "board": None}
    try:
        data = result.board.to_board().model_dump(by_alias=True)
    except ValueError as error:
        raise HTTPException(status_code=502, detail=f"The AI returned an invalid board: {error}")
    db.save_board(username, data)
    return {"reply": result.reply, "board": data}


if STATIC_DIR.is_dir():
    app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="static")
