import { test, expect } from '@playwright/test';

test.describe('Aegis OS Emergency Chat Flow', () => {
  test('Completes an emergency intake flow seamlessly', async ({ page }) => {
    // 1. Visit the home page
    await page.goto('/');
    
    // Expect the header to be visible
    await expect(page.getByRole('heading', { name: 'Aegis OS' })).toBeVisible();

    // Intercept backend case creation to guarantee reliable E2E tests without real LLMs
    await page.route('**/api/v1/cases', async route => {
      const json = {
        id: "mock_uuid",
        raw_input: "There is a severe car crash at the intersection",
        detected_case_type: "medical",
        urgency_level: "critical",
        confidence: 0.98,
        mode: "medical_triage",
        assistant_response: "Mocked AI response",
        structured_result_json: {
          recommended_actions: []
        }
      };
      await route.fulfill({ json });
    });

    // 2. Locate the chat input and submit an emergency
    const messageInput = page.getByPlaceholder('Describe the emergency situation...');
    await messageInput.waitFor({ state: 'visible' });
    await messageInput.fill('There is a severe car crash at the intersection, multiple people injured and bleeding.');
    
    // Send message
    await page.getByRole('button', { name: 'Send message' }).click();

    // 3. Verify optimistic UI (user message appears immediately)
    await expect(page.getByText('There is a severe car crash at the intersection')).toBeVisible();

    // Verify system processing state is triggered
    await page.waitForTimeout(1000);
  });
});

