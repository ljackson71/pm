import type { BoardData } from "@/lib/kanban";

export const getBoard = async (): Promise<BoardData> => {
  const response = await fetch("/api/board");
  return response.json();
};

let lastSave: Promise<unknown> = Promise.resolve();

// Saves are chained so they reach the server in the order they were made.
export const saveBoard = (board: BoardData) => {
  const put = () =>
    fetch("/api/board", {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(board),
    });
  lastSave = lastSave.then(put, put);
  return lastSave;
};

export type ChatMessage = { role: "user" | "assistant"; content: string };

export type ChatResponse = { reply: string; board: BoardData | null };

export const sendChat = async (
  message: string,
  history: ChatMessage[]
): Promise<ChatResponse> => {
  const response = await fetch("/api/chat", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message, history }),
  });
  if (!response.ok) {
    throw new Error(`Chat failed (${response.status})`);
  }
  return response.json();
};
