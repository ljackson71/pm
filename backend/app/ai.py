from openai import OpenAI
from pydantic import BaseModel

from app.models import Board, Card, ChatMessage, Column

MODEL = "gpt-5.4-mini"

INSTRUCTIONS = """You are the assistant in a Kanban project management app. You help the user \
understand and change their board.

The board has ordered columns, each with an id and a title. Cards are listed in board order; each \
card has an id, a title, details, and column_id: the id of the column it is in. A card's position \
within its column follows its order in the cards list.

Rules:
- Reply to the user in `reply`. Keep it short.
- If the user asks to change the board, return the complete updated board in `board`. \
Otherwise set `board` to null.
- Columns are fixed: never add or remove columns or change their ids. You may rename them.
- Move a card by changing its column_id (and its position in the list for ordering).
- Keep existing card ids unchanged. Give new cards a unique id like "card-<short random text>".
- When creating a card without details from the user, write a brief one-line description.

Current board:
"""


class ChatColumn(BaseModel):
    id: str
    title: str


class ChatCard(BaseModel):
    id: str
    title: str
    details: str
    column_id: str


class ChatBoard(BaseModel):
    """The board as the AI sees it. Each card names its column, so a card cannot end up in
    two columns, and cards are a list because Structured Outputs cannot express a dict keyed
    by id."""

    columns: list[ChatColumn]
    cards: list[ChatCard]

    @classmethod
    def from_board(cls, board: Board) -> "ChatBoard":
        return cls(
            columns=[ChatColumn(id=column.id, title=column.title) for column in board.columns],
            cards=[
                ChatCard(**board.cards[card_id].model_dump(), column_id=column.id)
                for column in board.columns
                for card_id in column.card_ids
            ],
        )

    def to_board(self) -> Board:
        unknown = {card.column_id for card in self.cards} - {column.id for column in self.columns}
        if unknown:
            raise ValueError(f"Cards reference unknown columns: {sorted(unknown)}")
        if len({card.id for card in self.cards}) != len(self.cards):
            raise ValueError("Duplicate card ids")
        return Board(
            columns=[
                Column(
                    id=column.id,
                    title=column.title,
                    cardIds=[card.id for card in self.cards if card.column_id == column.id],
                )
                for column in self.columns
            ],
            cards={
                card.id: Card(id=card.id, title=card.title, details=card.details)
                for card in self.cards
            },
        )


class ChatResult(BaseModel):
    reply: str
    board: ChatBoard | None


def client() -> OpenAI:
    # Reads OPENAI_API_KEY from the environment.
    return OpenAI()


def chat(board: Board, history: list[ChatMessage], message: str) -> ChatResult:
    board_json = ChatBoard.from_board(board).model_dump_json()
    response = client().responses.parse(
        model=MODEL,
        instructions=INSTRUCTIONS + board_json,
        input=[
            *(entry.model_dump() for entry in history),
            {"role": "user", "content": message},
        ],
        text_format=ChatResult,
    )
    return response.output_parsed
