import { expect, test } from "@playwright/test";
import { signInWithDemoBoard } from "./helpers";

test("AI adds a card that appears without reload and persists", async ({ page }) => {
  test.skip(!process.env.OPENAI_API_KEY, "OPENAI_API_KEY not set");
  test.setTimeout(120_000);
  await signInWithDemoBoard(page);

  await page.getByRole("button", { name: "Open AI chat" }).click();
  const sidebar = page.getByRole("complementary", { name: "AI chat" });
  await sidebar.getByLabel("Message").fill('Add a card called "Chat e2e card" to Review');
  await sidebar.getByRole("button", { name: "Send" }).click();

  const review = page.getByTestId("column-col-review");
  await expect(review.getByText("Chat e2e card")).toBeVisible({ timeout: 60_000 });
  await expect(sidebar.getByRole("status")).toHaveCount(0);

  await page.reload();
  await expect(review.getByText("Chat e2e card")).toBeVisible();
});
