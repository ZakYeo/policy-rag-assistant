import { expect, test } from '@playwright/test';
import { answer } from '../src/test/fixtures';

test('responds with real API-shaped evidence and adapts when resized', async ({ page }, info) => {
  const failures: string[] = [];
  page.on('pageerror', (error) => failures.push(error.message));
  await page.route('**/api/ask', (route) => route.fulfill({ json: answer }));
  await page.setViewportSize({ width: 1572, height: 1000 });
  await page.goto('/');
  await page.getByRole('textbox', { name: 'Your question' }).fill('Can I put customer data into a public AI tool?');
  await page.getByRole('button', { name: 'Ask a question', exact: true }).click();
  await expect(page.locator('.answer-text')).toHaveText(answer.answer);
  await expect(page.getByRole('heading', { name: 'Policy references' })).toBeVisible();
  await expect(page.getByText(answer.sources[0].chunk_id, { exact: false })).toBeVisible();
  await page.screenshot({ path: info.outputPath('desktop-light.png'), fullPage: true });
  for (const [width, height] of [[320, 720], [390, 844], [768, 1024], [844, 390], [1440, 500], [1920, 1080]]) {
    await page.setViewportSize({ width, height });
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true);
    await expect(page.getByRole('textbox', { name: 'Your question' })).toBeVisible();
    await expect(page.getByRole('button', { name: 'Ask a question', exact: true })).toBeVisible();
    await expect(page.locator('.answer-text')).toHaveText(answer.answer);
  }
  await page.setViewportSize({ width: 390, height: 844 });
  await page.screenshot({ path: info.outputPath('mobile-light.png'), fullPage: true });
  await page.getByRole('button', { name: 'Switch to dark mode' }).click();
  for (const [width, height] of [[320, 720], [768, 1024], [844, 390], [1572, 1000]]) {
    await page.setViewportSize({ width, height });
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true);
    await expect(page.locator('.answer-text')).toHaveText(answer.answer);
  }
  await page.screenshot({ path: info.outputPath('desktop-dark.png'), fullPage: true });
  expect(failures).toEqual([]);
});

test('follows system theme until toggled and remembers the override', async ({ page }) => {
  await page.emulateMedia({ colorScheme: 'dark' });
  await page.goto('/');
  await expect(page.locator('html')).toHaveAttribute('data-theme', 'dark');
  await page.emulateMedia({ colorScheme: 'light' });
  await expect(page.locator('html')).toHaveAttribute('data-theme', 'light');
  await page.getByRole('button', { name: 'Switch to dark mode' }).click();
  await page.reload();
  await expect(page.locator('html')).toHaveAttribute('data-theme', 'dark');
  await expect(page.getByRole('button', { name: 'Switch to light mode' })).toBeVisible();
});

test('validates blank input and renders extractive content safely', async ({ page }) => {
  await page.goto('/');
  await page.getByRole('button', { name: 'Ask a question', exact: true }).click();
  await expect(page.getByRole('alert')).toContainText('Please enter a question');
  await page.route('**/api/ask', async (route) => {
    expect(route.request().postDataJSON().answer_provider).toBe('extractive');
    await route.fulfill({ json: { ...answer, answer: '<img src=x onerror="alert(1)">', answer_provider: 'extractive' } });
  });
  await page.getByRole('radio', { name: 'Direct policy extracts (Extractive)' }).check();
  await page.getByRole('textbox', { name: 'Your question' }).fill('What does the policy say?');
  await page.getByRole('button', { name: 'Ask a question', exact: true }).click();
  await expect(page.locator('.answer-text')).toContainText('<img');
  await expect(page.locator('img')).toHaveCount(0);
});

test('shows skeletons and keeps form and theme usable while waiting', async ({ page }, info) => {
  let release!: () => void;
  const gate = new Promise<void>((resolve) => { release = resolve; });
  await page.route('**/api/ask', async (route) => { await gate; await route.fulfill({ json: answer }); });
  await page.goto('/');
  await page.getByRole('textbox', { name: 'Your question' }).fill('Can I use AI?');
  await page.getByRole('button', { name: 'Ask a question', exact: true }).click();
  try {
    await expect(page.getByTestId('skeleton').first()).toBeVisible();
    await expect(page.getByRole('button', { name: 'Checking policies…' })).toBeDisabled();
    await page.getByRole('textbox', { name: 'Your question' }).fill('My next question');
    await page.getByRole('button', { name: 'Switch to dark mode' }).click();
    await page.setViewportSize({ width: 390, height: 600 });
    await page.emulateMedia({ reducedMotion: 'reduce' });
    expect(await page.getByTestId('skeleton').first().evaluate((element) => getComputedStyle(element).animationName)).toBe('none');
    await page.screenshot({ path: info.outputPath('mobile-dark-loading.png'), fullPage: true });
  } finally { release(); }
  await expect(page.locator('.answer-text')).toHaveText(answer.answer);
  await expect(page.getByTestId('skeleton')).toHaveCount(0);
  await expect(page.getByRole('textbox', { name: 'Your question' })).toHaveValue('My next question');
});
