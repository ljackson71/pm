from typing import Self

from pydantic import BaseModel, Field, model_validator


class Card(BaseModel):
    id: str
    title: str
    details: str


class Column(BaseModel):
    id: str
    title: str
    card_ids: list[str] = Field(alias="cardIds")


class Board(BaseModel):
    columns: list[Column]
    cards: dict[str, Card]

    @model_validator(mode="after")
    def card_ids_exist(self) -> Self:
        for column in self.columns:
            missing = set(column.card_ids) - self.cards.keys()
            if missing:
                raise ValueError(f"Column {column.id} references unknown cards: {sorted(missing)}")
        return self
