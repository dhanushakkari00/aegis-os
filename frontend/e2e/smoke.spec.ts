import { test, expect } from "@playwright/test";

test("landing page smoke test", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByRole("heading", { name: /emergency intelligence/i })).toBeVisible();
  await expect(page.getByLabel("Analysis mode")).toBeVisible();
  await expect(page.getByLabel("Emergency intake message")).toBeVisible();
  await expect(page.getByRole("button", { name: /Attach files/i })).toBeVisible();
  await expect(page.getByRole("button", { name: /Send message/i })).toBeDisabled();
});
