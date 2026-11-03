import { expect, test } from '@playwright/test';
import { evaluationMetadata, evaluationRun } from '../src/test/evaluationFixtures';

test('shows persisted metrics, explanations, judge evidence and Markdown on refresh', async ({ page }, info) => {
  let starts = 0;
  await page.route('**/api/evaluations**', (route) => {
    const path = new URL(route.request().url()).pathname;
    if (route.request().method() === 'POST') starts++;
    return route.fulfill({ json: path === '/api/evaluations' ? evaluationMetadata : path === '/api/evaluations/runs' ? [evaluationRun] : evaluationRun });
  });
  await page.goto('/evaluations');
  await expect(page.getByRole('heading', { name: 'RAG evaluation', exact: true })).toBeVisible();
  await expect(page.getByText('completed · 36/36 answer attempts processed')).toBeVisible();
  await expect(page.getByText('Higher:', { exact: true })).toHaveCount(5);
  await expect(page.getByText('Lower:', { exact: true })).toHaveCount(5);
  await page.getByText('Can I paste customer data into public AI?', { exact: false }).click();
  await expect(page.locator('.answer-text code')).toHaveCount(2);
  await expect(page.getByText('The cited policy supports the prohibition.')).toHaveCount(8);
  await expect(page.getByText('Reviewed reference answer')).toBeVisible();
  for (const width of [1440, 320]) {
    await page.setViewportSize({ width, height: 1000 });
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true);
    await page.screenshot({ path: info.outputPath(`evaluation-${width}.png`), fullPage: true });
  }
  await page.reload();
  await expect(page.getByText('completed · 36/36 answer attempts processed')).toBeVisible();
  expect(starts).toBe(0);
});

test('starts only explicitly and reconnects to persisted progress', async ({ page }) => {
  let started = false;
  const running = { ...evaluationRun, status: 'running', stage: 'Evaluating', progress: 2, rows: [], summary: {} };
  await page.route('**/api/evaluations**', (route) => {
    const path = new URL(route.request().url()).pathname;
    if (route.request().method() === 'POST') { started = true; return route.fulfill({ json: running, status: 202 }); }
    return route.fulfill({ json: path === '/api/evaluations' ? evaluationMetadata : path === '/api/evaluations/runs' ? started ? [running] : [] : running });
  });
  await page.goto('/evaluations');
  await expect(page.getByText('No saved evaluations yet.', { exact: false })).toBeVisible();
  await page.getByRole('button', { name: 'Run evaluation', exact: true }).click();
  await expect(page.getByRole('progressbar')).toHaveAttribute('value', '2');
  await expect(page.getByRole('button', { name: 'Evaluation in progress' })).toBeDisabled();
  await page.reload();
  await expect(page.getByRole('progressbar')).toHaveAttribute('value', '2');
});

test('shows a five-answer run with one configuration and five scored samples', async ({ page }) => {
  const metadata = { ...evaluationMetadata, case_count: 5, eligible_count: 5 };
  const run = {
    ...evaluationRun, progress: 5, total: 5, dataset_version: 'northstar-progressive-5-v2',
    configuration: { ...evaluationRun.configuration, presets: { standard: 4 } },
    rows: [evaluationRun.rows[0]],
    summary: Object.fromEntries(Object.keys(evaluationMetadata.metrics).map(key => [key, {
      standard: 0.8, limited: null, delta: null, sample_count: 5, paired_count: 0, scored_counts: { standard: 5 },
    }])),
  };
  await page.route('**/api/evaluations**', route => {
    const path = new URL(route.request().url()).pathname;
    return route.fulfill({ json: path === '/api/evaluations' ? metadata : path === '/api/evaluations/runs' ? [run] : run });
  });
  await page.goto('/evaluations');
  await expect(page.getByText('completed · 5/5 answer attempts processed')).toBeVisible();
  await expect(page.getByText('5/5 questions scored', { exact: false })).toHaveCount(5);
  await page.getByText('Can I paste customer data into public AI?', { exact: false }).click();
  await expect(page.locator('.answer-text code')).toHaveCount(1);
});
