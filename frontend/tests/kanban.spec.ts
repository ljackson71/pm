import { expect, test } from "@playwright/test";
import { dragCard, signIn, signInWithDemoBoard } from "./helpers";

test.beforeEach(async ({ page }) => {
  await signInWithDemoBoard(page);
});

test("loads the kanban board", async ({ page }) => {
  await expect(page.getByRole("heading", { name: "Kanban Studio" })).toBeVisible();
  await expect(page.locator('[data-testid^="column-"]')).toHaveCount(5);
});

test("adds a card to a column", async ({ page }) => {
  const firstColumn = page.locator('[data-testid^="column-"]').first();
  await firstColumn.getByRole("button", { name: /add a card/i }).click();
  await firstColumn.getByPlaceholder("Card title").fill("Playwright card");
  await firstColumn.getByPlaceholder("Details").fill("Added via e2e.");
  await firstColumn.getByRole("button", { name: /add card/i }).click();
  await expect(firstColumn.getByText("Playwright card")).toBeVisible();
});

test("moves a card between columns", async ({ page }) => {
  await dragCard(page, "card-1", "col-review");
  await expect(page.getByTestId("column-col-review").getByTestId("card-card-1")).toBeVisible();
});

test("changes persist across reload and signing in again", async ({ page }) => {
  const backlog = page.getByTestId("column-col-backlog");
  const review = page.getByTestId("column-col-review");
  const discovery = page.getByTestId("column-col-discovery");

  await backlog.getByRole("button", { name: /add a card/i }).click();
  await backlog.getByPlaceholder("Card title").fill("Persisted card");
  await backlog.getByPlaceholder("Details").fill("Survives reload.");
  await backlog.getByRole("button", { name: /add card/i }).click();

  await backlog.getByRole("button", { name: "Edit Gather customer signals", exact: true }).click();
  await backlog.getByLabel("Edit title").fill("Edited title");
  await backlog.getByLabel("Edit details").fill("Edited details");
  await backlog.getByRole("button", { name: "Save" }).click();

  await dragCard(page, "card-1", "col-review");
  await expect(review.getByTestId("card-card-1")).toBeVisible();

  await discovery.getByLabel("Column title").fill("Research");
  await discovery.getByLabel("Column title").press("Enter");

  await page.getByRole("button", { name: "Delete Prototype analytics view", exact: true }).click();

  const expectChanges = async () => {
    await expect(backlog.getByText("Persisted card")).toBeVisible();
    await expect(backlog.getByText("Edited title")).toBeVisible();
    await expect(backlog.getByText("Edited details")).toBeVisible();
    await expect(review.getByTestId("card-card-1")).toBeVisible();
    await expect(backlog.getByTestId("card-card-1")).toHaveCount(0);
    await expect(discovery.getByLabel("Column title")).toHaveValue("Research");
    await expect(page.getByText("Prototype analytics view")).toHaveCount(0);
  };

  // Saves are async; wait until the last change (the delete) reaches the server.
  await expect
    .poll(async () => Object.keys((await (await page.request.get("/api/board")).json()).cards))
    .not.toContain("card-3");

  await page.reload();
  await expectChanges();

  await page.getByRole("button", { name: "Log out" }).click();
  await signIn(page);
  await expectChanges();
});
