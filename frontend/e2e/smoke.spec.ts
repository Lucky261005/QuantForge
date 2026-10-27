import { expect, test } from "@playwright/test";

// Read-only walk through the core workflows. Uses the seeded demo account unless overridden.
const EMAIL = process.env.E2E_EMAIL ?? "demo@quantforge.io";
const PASSWORD = process.env.E2E_PASSWORD ?? "DemoPass123";

test.beforeEach(async ({ page }) => {
  await page.goto("/login");
  await page.getByLabel("Email").fill(EMAIL);
  await page.getByLabel("Password", { exact: true }).fill(PASSWORD);
  await page.getByRole("button", { name: "Log in" }).click();
  await expect(page).toHaveURL(/\/dashboard/);
});

test("dashboard shows market panels anchored to the stored data", async ({ page }) => {
  await expect(page.getByText("Market overview")).toBeVisible();
  await expect(page.getByText(/Last close in data:/).first()).toBeVisible();
});

test("a completed backtest opens with metrics, walk-forward and cost sensitivity", async ({ page }) => {
  await page.goto("/backtests");
  await page.getByRole("link", { name: "View" }).first().click();
  await expect(page.getByText("Total return")).toBeVisible();

  await page.getByRole("tab", { name: "Walk-forward" }).click();
  await expect(page.getByRole("tabpanel").locator("tbody tr").first()).toBeVisible({ timeout: 30_000 });

  await page.getByRole("tab", { name: "Cost Sensitivity" }).click();
  await expect(page.getByRole("tabpanel").getByText("(as run)")).toBeVisible({ timeout: 30_000 });
});

test("paper portfolio page loads", async ({ page }) => {
  await page.goto("/portfolio");
  await expect(page.getByText("Record a transaction")).toBeVisible();
  await expect(page.getByText(/Nothing here places a real order/)).toBeVisible();
});

test("a wrong password shows an error instead of reloading", async ({ page, context }) => {
  await context.clearCookies();
  await page.evaluate(() => localStorage.clear());
  await page.goto("/login");
  await page.getByLabel("Email").fill(EMAIL);
  await page.getByLabel("Password", { exact: true }).fill("definitely-wrong");
  await page.getByRole("button", { name: "Log in" }).click();
  await expect(page.getByText(/incorrect email or password/i)).toBeVisible();
  await expect(page).toHaveURL(/\/login/);
});
