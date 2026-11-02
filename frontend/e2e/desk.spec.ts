import { expect, test } from '@playwright/test';
import { answer } from '../src/test/fixtures';

test('responds with real API-shaped evidence and adapts when resized', async ({ page }, info) => {
  const failures: string[] = [];
  page.on('pageerror', (error) => failures.push(error.message));
  await page.route('**/api/ask', (route) => route.fulfill({ json: answer }));
  await page.route('**/api/ask/stream', (route) => route.fulfill({ contentType: 'text/event-stream', body: `event: delta\ndata: ${JSON.stringify({ text: answer.answer })}\n\nevent: result\ndata: ${JSON.stringify(answer)}\n\n` }));
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
  await page.getByRole('radio', { name: 'Direct policy extracts (Extractive)' }).check();
  await page.getByRole('textbox', { name: 'Your question' }).fill('Can I use AI?');
  await page.getByRole('button', { name: 'Ask a question', exact: true }).click();
  try {
    await expect(page.getByTestId('skeleton').first()).toBeVisible();
    await expect(page.getByRole('button', { name: 'Checking policies…' })).toBeDisabled();
    await page.getByRole('textbox', { name: 'Your question' }).fill('My next question');
    await expect(page.getByText('Answer for: Can I use AI?')).toBeVisible();
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

test('streams text over HTTP before completion and retains state while resized', async ({ page, request }, info) => {
  await page.goto('/');
  await page.getByRole('textbox', { name: 'Your question' }).fill('stream success');
  await page.getByRole('button', { name: 'Ask a question', exact: true }).click();
  try {
    await expect(page.locator('.answer-text')).toHaveText('First part. ');
    await expect(page.getByTestId('skeleton').first()).toBeVisible();
    await expect(page.getByRole('button', { name: 'Checking policies…' })).toBeDisabled();
    for (const [width, height] of [[320, 700], [844, 390], [1572, 1000]]) {
      await page.setViewportSize({ width, height });
      expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
      await expect(page.locator('.answer-text')).toHaveText('First part. ');
    }
    await page.getByRole('button', { name: 'Switch to dark mode' }).click();
    await page.screenshot({ path: info.outputPath('stream-in-progress.png'), fullPage: true });
  } finally { expect((await request.post('/__test__/release/success')).ok()).toBe(true); }
  await expect(page.locator('.answer-text')).toHaveText('First part. Complete answer.');
  await expect(page.getByTestId('skeleton')).toHaveCount(0);
  await expect(page.getByText('Chunk: test-p1-c0')).toBeVisible();
  await expect(page.getByRole('button', { name: 'Ask a question', exact: true })).toBeEnabled();
});

test('keeps interrupted streamed text clearly incomplete and allows a new submission', async ({ page, request }) => {
  await page.goto('/');
  await page.getByRole('textbox', { name: 'Your question' }).fill('stream failure');
  await page.getByRole('button', { name: 'Ask a question', exact: true }).click();
  await expect(page.locator('.answer-text')).toHaveText('First part. ');
  expect((await request.post('/__test__/release/failure')).ok()).toBe(true);
  await expect(page.getByRole('alert')).toContainText('could not be completed');
  await expect(page.getByText('Incomplete answer — the response was interrupted.')).toBeVisible();
  await expect(page.locator('.answer-text')).toHaveText('First part. ');
  await expect(page.getByRole('textbox', { name: 'Your question' })).toHaveValue('stream failure');
  await expect(page.getByRole('button', { name: 'Ask a question', exact: true })).toBeEnabled();
});

test('extractive mode works against the real local policy index', async ({ page }) => {
  await page.goto('/');
  await page.getByRole('radio', { name: 'Direct policy extracts (Extractive)' }).check();
  await page.getByRole('textbox', { name: 'Your question' }).fill('Can I put customer data into a public AI tool?');
  await page.getByRole('button', { name: 'Ask a question', exact: true }).click();
  await expect(page.locator('.answer-text')).toContainText('Prohibited', { timeout: 15000 });
  await expect(page.getByRole('heading', { name: 'Policy references' })).toBeVisible();
  await expect(page.getByText('Extractive', { exact: true })).toBeVisible();
});

test('supports keyboard controls and has no extra product actions', async ({ page }) => {
  await page.goto('/');
  await page.keyboard.press('Tab');
  await expect(page.getByRole('link', { name: 'Skip to content' })).toBeFocused();
  await page.getByRole('button', { name: 'Switch to dark mode' }).focus();
  await page.keyboard.press('Space');
  await expect(page.locator('html')).toHaveAttribute('data-theme', 'dark');
  await page.getByRole('radio', { name: 'AI-assisted (OpenAI)' }).focus();
  await page.keyboard.press('ArrowRight');
  await expect(page.getByRole('radio', { name: 'Direct policy extracts (Extractive)' })).toBeChecked();
  await expect(page.getByRole('button')).toHaveCount(10);
  await expect(page.getByRole('link')).toHaveCount(3);
  await expect(page.getByRole('textbox')).toHaveCount(1);
  await expect(page.getByRole('radio')).toHaveCount(2);
});

test('sample questions float in the wide margin, reflow inline and only fill the editor', async ({ page }, info) => {
  let questionRequests = 0;
  page.on('request', (request) => { if (/\/api\/ask(?:\/stream)?$/.test(request.url())) questionRequests++; });
  await page.setViewportSize({ width: 1920, height: 700 });
  await page.goto('/');
  const samples = page.getByRole('complementary', { name: 'Sample Questions' });
  await expect(samples.getByRole('heading', { name: 'Everyday questions' })).toBeVisible();
  await expect(samples.getByRole('heading', { name: 'Across policies' })).toBeVisible();
  await expect(samples.getByRole('button')).toHaveCount(8);
  const form = page.getByRole('region', { name: 'Ask a policy question' });
  const formBox = (await form.boundingBox())!;
  const panelBox = (await samples.boundingBox())!;
  expect(panelBox.x).toBeGreaterThanOrEqual(16);
  expect(panelBox.x + panelBox.width).toBeLessThan(formBox.x);
  expect(await samples.evaluate((element) => getComputedStyle(element).position)).toBe('fixed');
  await page.evaluate(() => scrollTo(0, 400));
  expect((await samples.boundingBox())!.y).toBeCloseTo(panelBox.y, 0);
  await page.screenshot({ path: info.outputPath('samples-wide-light.png'), fullPage: true });
  await page.getByRole('radio', { name: 'Direct policy extracts (Extractive)' }).check();
  const basicQuestion = 'What are our core working hours?';
  await samples.getByRole('button', { name: basicQuestion, exact: true }).click();
  await expect(page.getByRole('textbox', { name: 'Your question' })).toHaveValue(basicQuestion);
  await expect(page.getByRole('textbox', { name: 'Your question' })).toBeFocused();
  await expect(page.getByRole('radio', { name: 'Direct policy extracts (Extractive)' })).toBeChecked();
  for (const [width, height] of [[1840, 700], [1839, 700], [1440, 800], [768, 1024], [390, 844], [320, 700], [844, 390]]) {
    await page.setViewportSize({ width, height });
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
    if (width < 1840) {
      const inlineBox = (await samples.boundingBox())!;
      const currentForm = (await form.boundingBox())!;
      expect(await samples.evaluate((element) => getComputedStyle(element).position)).not.toBe('fixed');
      expect(inlineBox.x).toBeCloseTo(currentForm.x, 0);
      expect(inlineBox.width).toBeCloseTo(currentForm.width, 0);
      expect(inlineBox.y).toBeGreaterThanOrEqual(currentForm.y + currentForm.height);
    }
  }
  await page.setViewportSize({ width: 390, height: 844 });
  await page.getByRole('button', { name: 'Switch to dark mode' }).click();
  const combinedQuestion = 'For remote work, what manager approval and information security controls do I need?';
  await samples.getByRole('button', { name: combinedQuestion, exact: true }).focus();
  await page.keyboard.press('Enter');
  await expect(page.getByRole('textbox', { name: 'Your question' })).toHaveValue(combinedQuestion);
  await expect(page.getByRole('textbox', { name: 'Your question' })).toBeFocused();
  await page.screenshot({ path: info.outputPath('samples-mobile-dark.png'), fullPage: true });
  expect(questionRequests).toBe(0);
});

test('wraps long content and shows honest empty-evidence results', async ({ page }) => {
  const longName = 'northstar-' + 'policy'.repeat(100) + '.pdf';
  await page.route('**/api/ask', (route) => route.fulfill({ json: {
    ...answer, answer_provider: 'extractive', answer: 'longword'.repeat(500),
    sources: [{ ...answer.sources[0], document_name: longName, chunk_id: 'chunk'.repeat(100) }],
    routed_documents: [], retrieved_chunks: [],
  } }));
  await page.setViewportSize({ width: 320, height: 700 });
  await page.goto('/');
  await page.getByRole('radio', { name: 'Direct policy extracts (Extractive)' }).check();
  await page.getByRole('textbox', { name: 'Your question' }).fill('Long answer');
  await page.getByRole('button', { name: 'Ask a question', exact: true }).click();
  await expect(page.locator('.answer-text')).toBeVisible();
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
  await page.route('**/api/ask', (route) => route.fulfill({ json: { ...answer, answer_provider: 'extractive', answer: 'No policy context was found.', sources: [], routed_documents: [], retrieved_chunks: [] } }));
  await page.getByRole('button', { name: 'Ask a question', exact: true }).click();
  await expect(page.locator('.answer-text')).toHaveText('No policy context was found.');
  await expect(page.getByText('No references were found for this answer.')).toBeVisible();
});
