import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { KanbanBoard } from "@/components/KanbanBoard";
import { getBoard, saveBoard } from "@/lib/api";
import type { BoardData } from "@/lib/kanban";

vi.mock("@/lib/api", () => ({
  getBoard: vi.fn(),
  saveBoard: vi.fn(),
}));

const board: BoardData = {
  columns: [
    { id: "col-a", title: "Todo", cardIds: ["card-1"] },
    { id: "col-b", title: "Done", cardIds: [] },
  ],
  cards: {
    "card-1": { id: "card-1", title: "Write tests", details: "With vitest" },
  },
};

const renderBoard = async () => {
  render(<KanbanBoard onLogout={() => {}} />);
  return screen.findByTestId("column-col-a");
};

const lastSaved = () => vi.mocked(saveBoard).mock.lastCall?.[0];

beforeEach(() => {
  vi.mocked(getBoard).mockResolvedValue(board);
  vi.mocked(saveBoard).mockReset();
});

describe("KanbanBoard", () => {
  it("renders the board from the API", async () => {
    await renderBoard();
    expect(screen.getAllByTestId(/^column-/)).toHaveLength(2);
    expect(screen.getByText("Write tests")).toBeInTheDocument();
    expect(saveBoard).not.toHaveBeenCalled();
  });

  it("renames a column on blur, not per keystroke", async () => {
    const column = await renderBoard();
    const input = within(column).getByLabelText("Column title");
    await userEvent.clear(input);
    await userEvent.type(input, "Backlog");
    expect(saveBoard).not.toHaveBeenCalled();

    await userEvent.tab();
    expect(saveBoard).toHaveBeenCalledTimes(1);
    expect(lastSaved()).toEqual({
      ...board,
      columns: [{ ...board.columns[0], title: "Backlog" }, board.columns[1]],
    });
  });

  it("renames a column on Enter", async () => {
    const column = await renderBoard();
    const input = within(column).getByLabelText("Column title");
    await userEvent.clear(input);
    await userEvent.type(input, "Backlog{Enter}");
    expect(lastSaved()?.columns[0].title).toBe("Backlog");
  });

  it("adds a card", async () => {
    const column = await renderBoard();
    await userEvent.click(within(column).getByRole("button", { name: /add a card/i }));
    await userEvent.type(within(column).getByPlaceholderText(/card title/i), "New card");
    await userEvent.type(within(column).getByPlaceholderText(/details/i), "Notes");
    await userEvent.click(within(column).getByRole("button", { name: /add card/i }));

    expect(within(column).getByText("New card")).toBeInTheDocument();
    const saved = lastSaved()!;
    const newId = saved.columns[0].cardIds[1];
    expect(saved.columns[0].cardIds).toEqual(["card-1", newId]);
    expect(saved.cards[newId]).toEqual({ id: newId, title: "New card", details: "Notes" });
  });

  it("edits a card's title and details", async () => {
    const column = await renderBoard();
    await userEvent.click(within(column).getByRole("button", { name: "Edit Write tests" }));
    const title = within(column).getByLabelText("Edit title");
    const details = within(column).getByLabelText("Edit details");
    await userEvent.clear(title);
    await userEvent.type(title, "Write more tests");
    await userEvent.clear(details);
    await userEvent.type(details, "With playwright");
    await userEvent.click(within(column).getByRole("button", { name: "Save" }));

    expect(within(column).getByText("Write more tests")).toBeInTheDocument();
    expect(within(column).getByText("With playwright")).toBeInTheDocument();
    expect(lastSaved()?.cards["card-1"]).toEqual({
      id: "card-1",
      title: "Write more tests",
      details: "With playwright",
    });
  });

  it("deletes a card", async () => {
    const column = await renderBoard();
    await userEvent.click(within(column).getByRole("button", { name: "Delete Write tests" }));

    expect(within(column).queryByText("Write tests")).not.toBeInTheDocument();
    expect(lastSaved()).toEqual({
      columns: [{ ...board.columns[0], cardIds: [] }, board.columns[1]],
      cards: {},
    });
  });
});
