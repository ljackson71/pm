import { defineConfig, devices } from "@playwright/test";

const baseURL = process.env.BASE_URL;

export default defineConfig({
  testDir: "./tests",
  timeout: 60_000,
  // Tests share one user's persisted board, so they must not run in parallel.
  workers: 1,
  expect: {
    timeout: 10_000,
  },
  use: {
    baseURL: baseURL ?? "http://127.0.0.1:3000",
    trace: "retain-on-failure",
  },
  webServer: baseURL
    ? undefined
    : [
        {
          command: "uv run --directory ../backend uvicorn app.main:app --port 8000",
          url: "http://localhost:8000/api/health",
          reuseExistingServer: true,
          timeout: 120_000,
        },
        {
          command: "npm run dev -- --hostname 127.0.0.1 --port 3000",
          url: "http://127.0.0.1:3000",
          reuseExistingServer: true,
          timeout: 120_000,
        },
      ],
  projects: [
    {
      name: "chromium",
      use: { ...devices["Desktop Chrome"] },
    },
  ],
});
