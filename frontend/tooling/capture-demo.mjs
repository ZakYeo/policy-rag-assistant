// Opt-in: one real question against a running app containing only public demo PDFs.
import { chromium, expect } from '@playwright/test';
import { createHash } from 'node:crypto';
import { mkdir, readFile, writeFile } from 'node:fs/promises';
import { fileURLToPath } from 'node:url';

const destination = fileURLToPath(new URL('../../docs/media/', import.meta.url));
const baseURL = process.env.DEMO_BASE_URL ?? 'http://127.0.0.1:8001';
const question = 'Can I put customer data into a public AI tool? Please answer briefly in three sentences, with policy citations.';
const filenames = ['northstar-ai-acceptable-use-policy.pdf', 'northstar-employee-handbook.pdf', 'northstar-information-security-policy.pdf'];
const policies = await (await fetch(`${baseURL}/api/policies`)).json();
expect(policies.map((policy) => policy.filename).sort()).toEqual([...filenames].sort());
for (const policy of policies) {
  const original = Buffer.from(await (await fetch(`${baseURL}/api/policies/${encodeURIComponent(policy.id)}/original`)).arrayBuffer());
  const publishedSample = await readFile(new URL(`../../documents/${policy.filename}`, import.meta.url));
  const hash = (bytes) => createHash('sha256').update(bytes).digest('hex');
  expect(hash(original)).toBe(hash(publishedSample));
}
await mkdir(destination, { recursive: true });
const browser = await chromium.launch({ headless: true });
const context = await browser.newContext({
  viewport: { width: 1440, height: 1000 }, colorScheme: 'light',
  recordVideo: { dir: destination, size: { width: 1440, height: 1000 } },
});
const page = await context.newPage();
const errors = [];
page.on('pageerror', (error) => errors.push(error.message));
try {
  await page.goto(baseURL);
  await page.evaluate(() => document.fonts.ready);
  await expect(page.getByRole('button', { name: 'Can I put customer data into a public AI tool?', exact: true })).toBeVisible();
  await page.waitForTimeout(900); // Intentional reading pauses for the demonstration.
  await page.getByLabel('Your question').pressSequentially(question, { delay: 28 });
  await page.waitForTimeout(700);
  const responsePromise = page.waitForResponse((response) => response.url().endsWith('/api/ask/stream'));
  await page.getByRole('button', { name: 'Ask a question', exact: true }).click();
  await page.getByRole('heading', { name: 'Your answer', exact: true }).evaluate((heading) => {
    window.scrollTo({ top: window.scrollY + heading.getBoundingClientRect().top - 100, behavior: 'smooth' });
  });
  const response = await responsePromise;
  expect(response.status()).toBe(200);
  expect(response.headers()['content-type']).toContain('text/event-stream');
  await page.waitForFunction(() => !!document.querySelector('.answer-text')?.textContent
    && !!document.querySelector('button[type="submit"]:disabled'), undefined, { timeout: 45000 });
  await expect(page.getByRole('button', { name: 'Ask a question', exact: true })).toBeEnabled({ timeout: 45000 });
  await expect(page.getByRole('alert')).toHaveCount(0);
  const events = (await response.text()).split('\n\n');
  const terminal = events.find((event) => event.startsWith('event: result\n'));
  expect(terminal).toBeTruthy();
  const result = JSON.parse(terminal.split('\ndata: ')[1]);
  expect(result.answer_provider).toBe('openai');
  expect(result.sources.length).toBeGreaterThan(0);
  await expect(page.locator('.answer-text')).toHaveText(result.answer);
  await expect(page.locator('.answer-text')).toBeInViewport({ ratio: 0.5 });
  await page.waitForTimeout(3500);
  await page.screenshot({ path: `${destination}/policy-desk-light.png`, fullPage: true });
  await page.getByRole('button', { name: 'Switch to dark mode' }).click();
  await page.screenshot({ path: `${destination}/policy-desk-dark.png`, fullPage: true });
  await page.setViewportSize({ width: 390, height: 844 });
  await page.screenshot({ path: `${destination}/policy-desk-mobile-dark.png`, fullPage: true });
  await page.setViewportSize({ width: 1440, height: 1000 });
  await page.getByRole('button', { name: 'Switch to light mode' }).click();
  await page.getByRole('link', { name: 'Manage policies', exact: true }).click();
  await page.getByRole('button', { name: /AI Acceptable Use Policy.*pdf/ }).click();
  await page.getByRole('button', { name: 'Chunking settings', exact: true }).click();
  await page.screenshot({ path: `${destination}/manage-policies-light.png`, fullPage: true });
  await page.waitForTimeout(1500);
  await page.getByRole('link', { name: 'Ask policies', exact: true }).click();
  await page.getByRole('heading', { name: 'Your answer', exact: true }).evaluate((heading) => {
    window.scrollTo({ top: window.scrollY + heading.getBoundingClientRect().top - 100, behavior: 'smooth' });
  });
  await page.waitForTimeout(1500);
  expect(errors).toEqual([]);
  const video = page.video();
  await context.close();
  await video.saveAs(`${destination}/live-question-demo.webm`);
  await video.delete();
  await writeFile(`${destination}/capture-summary.json`, JSON.stringify({
    capturedAt: new Date().toISOString(), question, answerProvider: result.answer_provider,
    streamedBeforeCompletion: true, sourceCount: result.sources.length,
    consultedPolicies: result.routed_documents.map((policy) => policy.title),
    video: 'live-question-demo.webm', browserErrors: errors,
  }, null, 2) + '\n');
  console.log(`Captured live answer, ${result.sources.length} sources, screenshots and video in docs/media.`);
} finally {
  await context.close();
  await browser.close();
}
