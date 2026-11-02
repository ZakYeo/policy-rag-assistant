import { expect, test } from '@playwright/test';

test('real OpenAI text appears before completion with grounded policy evidence', async ({ page }, info) => {
  const failures: string[] = [];
  page.on('pageerror', (error) => failures.push(error.message));
  await page.goto('/');
  await page.getByRole('textbox', { name: 'Your question' }).fill('Explain the policy on public AI tools and customer data, citing the relevant pages.');
  const response = page.waitForResponse((response) => response.url().endsWith('/api/ask/stream'));
  await page.getByRole('button', { name: 'Ask a question', exact: true }).click();
  expect((await response).headers()['content-type']).toContain('text/event-stream');
  await expect(page.locator('.answer-text')).toBeVisible({ timeout: 45000 });
  await expect(page.getByRole('button', { name: 'Checking policies…' })).toBeDisabled();
  await page.screenshot({ path: info.outputPath('live-streaming.png'), fullPage: true });
  await expect(page.getByRole('button', { name: 'Ask a question', exact: true })).toBeEnabled({ timeout: 45000 });
  await expect(page.getByRole('alert')).toHaveCount(0);
  await expect(page.locator('.answer-text')).toContainText(/customer/i);
  await expect(page.getByRole('heading', { name: 'Policy references' })).toBeVisible();
  await expect(page.getByText('OpenAI', { exact: true })).toBeVisible();
  await expect(page.getByTestId('skeleton')).toHaveCount(0);
  await page.screenshot({ path: info.outputPath('live-completed.png'), fullPage: true });
  expect(failures).toEqual([]);
});
