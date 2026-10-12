import {
  addCard,
  deleteCard,
  moveCard,
  renameColumn,
  updateCard,
  type BoardData,
  type Column,
} from "@/lib/kanban";

describe("moveCard", () => {
  const baseColumns: Column[] = [
    { id: "col-a", title: "A", cardIds: ["card-1", "card-2"] },
    { id: "col-b", title: "B", cardIds: ["card-3"] },
  ];

  it("reorders cards in the same column", () => {
    const result = moveCard(baseColumns, "card-2", "card-1");
    expect(result[0].cardIds).toEqual(["card-2", "card-1"]);
  });

  it("moves cards to another column", () => {
    const result = moveCard(baseColumns, "card-2", "card-3");
    expect(result[0].cardIds).toEqual(["card-1"]);
    expect(result[1].cardIds).toEqual(["card-2", "card-3"]);
  });

  it("drops cards to the end of a column", () => {
    const result = moveCard(baseColumns, "card-1", "col-b");
    expect(result[0].cardIds).toEqual(["card-2"]);
    expect(result[1].cardIds).toEqual(["card-3", "card-1"]);
  });
});

describe("board mutations", () => {
  const board: BoardData = {
    columns: [
      { id: "col-a", title: "A", cardIds: ["card-1"] },
      { id: "col-b", title: "B", cardIds: [] },
    ],
    cards: { "card-1": { id: "card-1", title: "One", details: "First" } },
  };

  it("renames a column", () => {
    expect(renameColumn(board, "col-b", "Done").columns[1].title).toBe("Done");
  });

  it("adds a card to the end of a column", () => {
    const card = { id: "card-2", title: "Two", details: "" };
    const result = addCard(board, "col-a", card);
    expect(result.columns[0].cardIds).toEqual(["card-1", "card-2"]);
    expect(result.cards["card-2"]).toEqual(card);
  });

  it("updates a card", () => {
    const card = { id: "card-1", title: "Uno", details: "Primero" };
    expect(updateCard(board, card).cards["card-1"]).toEqual(card);
  });

  it("deletes a card from cards and its column", () => {
    const result = deleteCard(board, "card-1");
    expect(result.cards).toEqual({});
    expect(result.columns[0].cardIds).toEqual([]);
  });
});
