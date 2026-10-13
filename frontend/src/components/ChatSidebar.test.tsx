import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { KanbanBoard } from "@/components/KanbanBoard";
import { getBoard, saveBoard, sendChat, type ChatResponse } from "@/lib/api";
import type { BoardData } from "@/lib/kanban";

vi.mock("@/lib/api", () => ({
  getBoard: vi.fn(),
  saveBoard: vi.fn(),
  sendChat: vi.fn(),
}));

const board: BoardData = {
  columns: [{ id: "col-a", title: "Todo", cardIds: ["card-1"] }],
  cards: { "card-1": { id: "card-1", title: "Write tests", details: "" } },
};

const renderBoard = async () => {
  render(<KanbanBoard onLogout={() => {}} />);
  await screen.findByTestId("column-col-a");
  await userEvent.click(screen.getByRole("button", { name: "Open AI chat" }));
  return within(screen.getByRole("complementary", { name: "AI chat" }));
};

const send = async (sidebar: ReturnType<typeof within>, message: string) => {
  await userEvent.type(sidebar.getByLabelText("Message"), message);
  await userEvent.click(sidebar.getByRole("button", { name: "Send" }));
};

beforeEach(() => {
  vi.mocked(getBoard).mockResolvedValue(board);
  vi.mocked(saveBoard).mockReset();
  vi.mocked(sendChat).mockReset();
});

describe("ChatSidebar", () => {
  it("shows the user message, a pending state, then the reply", async () => {
    let respond!: (response: ChatResponse) => void;
    vi.mocked(sendChat).mockReturnValue(new Promise((resolve) => (respond = resolve)));
    const sidebar = await renderBoard();

    await send(sidebar, "Hello");

    expect(sidebar.getByText("Hello")).toBeInTheDocument();
    expect(sidebar.getByRole("status")).toHaveTextContent("Thinking...");
    expect(sendChat).toHaveBeenCalledWith("Hello", []);

    respond({ reply: "Hi there", board: null });

    expect(await sidebar.findByText("Hi there")).toBeInTheDocument();
    expect(sidebar.queryByRole("status")).not.toBeInTheDocument();
  });

  it("sends the conversation history with each message", async () => {
    vi.mocked(sendChat).mockResolvedValue({ reply: "Hi there", board: null });
    const sidebar = await renderBoard();

    await send(sidebar, "Hello");
    await sidebar.findByText("Hi there");
    await send(sidebar, "Thanks");

    expect(sendChat).toHaveBeenLastCalledWith("Thanks", [
      { role: "user", content: "Hello" },
      { role: "assistant", content: "Hi there" },
    ]);
  });

  it("updates the board when the response includes one", async () => {
    vi.mocked(sendChat).mockResolvedValue({
      reply: "Done.",
      board: {
        columns: [{ id: "col-a", title: "Backlog", cardIds: ["card-1", "card-2"] }],
        cards: {
          ...board.cards,
          "card-2": { id: "card-2", title: "From AI", details: "Added by chat" },
        },
      },
    });
    const sidebar = await renderBoard();

    await send(sidebar, "Add a card");

    const column = screen.getByTestId("column-col-a");
    expect(await within(column).findByText("From AI")).toBeInTheDocument();
    expect(within(column).getByLabelText("Column title")).toHaveValue("Backlog");
    expect(saveBoard).not.toHaveBeenCalled();
  });

  it("shows an error when the request fails", async () => {
    vi.mocked(sendChat).mockRejectedValue(new Error("Chat failed (502)"));
    const sidebar = await renderBoard();

    await send(sidebar, "Hello");

    expect(await sidebar.findByText(/something went wrong/i)).toBeInTheDocument();
    expect(sidebar.queryByRole("status")).not.toBeInTheDocument();
  });

  it("starts closed and can be opened and hidden", async () => {
    render(<KanbanBoard onLogout={() => {}} />);
    await screen.findByTestId("column-col-a");
    expect(screen.queryByRole("complementary", { name: "AI chat" })).not.toBeInTheDocument();

    await userEvent.click(screen.getByRole("button", { name: "Open AI chat" }));
    await userEvent.click(screen.getByRole("button", { name: "Hide" }));
    expect(screen.queryByRole("complementary", { name: "AI chat" })).not.toBeInTheDocument();

    await userEvent.click(screen.getByRole("button", { name: "Open AI chat" }));
    expect(screen.getByRole("complementary", { name: "AI chat" })).toBeInTheDocument();
  });

  it("keeps the conversation when hidden and reopened", async () => {
    vi.mocked(sendChat).mockResolvedValue({ reply: "Hi there", board: null });
    const sidebar = await renderBoard();
    await send(sidebar, "Hello");
    await sidebar.findByText("Hi there");

    await userEvent.click(sidebar.getByRole("button", { name: "Hide" }));
    await userEvent.click(screen.getByRole("button", { name: "Open AI chat" }));

    const reopened = within(screen.getByRole("complementary", { name: "AI chat" }));
    expect(reopened.getByText("Hello")).toBeInTheDocument();
    expect(reopened.getByText("Hi there")).toBeInTheDocument();
  });
});
