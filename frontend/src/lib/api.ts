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
