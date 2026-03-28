import { test, expect } from "@playwright/test";

test("landing page smoke test", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByRole("heading", { name: /emergency intelligence built/i })).toBeVisible();
  await expect(page.getByRole("button", { name: /launch analysis/i })).toBeVisible();
});
