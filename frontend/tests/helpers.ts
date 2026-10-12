import { expect, type Page } from "@playwright/test";
import { initialData } from "../src/lib/kanban";

export const signIn = async (page: Page, password = "password") => {
  await page.goto("/");
  await page.getByLabel("Username").fill("user");
  await page.getByLabel("Password").fill(password);
  await page.getByRole("button", { name: "Sign in" }).click();
};

// Signs in and resets the user's persisted board to the demo data.
export const signInWithDemoBoard = async (page: Page) => {
  await signIn(page);
  await expect(page.getByRole("heading", { name: "Kanban Studio" })).toBeVisible();
  await page.request.put("/api/board", { data: initialData });
  await page.reload();
  await expect(page.getByTestId("card-card-1")).toBeVisible();
};

export const dragCard = async (page: Page, cardId: string, columnId: string) => {
  const card = page.getByTestId(`card-${cardId}`);
  const targetColumn = page.getByTestId(`column-${columnId}`);
  await card.scrollIntoViewIfNeeded();
  const cardBox = await card.boundingBox();
  const columnBox = await targetColumn.boundingBox();
  if (!cardBox || !columnBox) {
    throw new Error("Unable to resolve drag coordinates.");
  }

  await page.mouse.move(cardBox.x + cardBox.width / 2, cardBox.y + cardBox.height / 2);
  await page.mouse.down();
  await page.mouse.move(columnBox.x + columnBox.width / 2, columnBox.y + 120, {
    steps: 12,
  });
  await page.mouse.up();
};
