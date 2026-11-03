import { expect, test } from '@playwright/test';
import { evaluationMetadata, evaluationRun, evaluationRow } from '../src/test/evaluationFixtures';

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
  await page.getByRole('region', { name: 'Question results', exact: true }).getByText('Can I paste customer data into public AI?', { exact: false }).click();
  await expect(page.getByRole('region', { name: 'Question results', exact: true }).locator('.answer-text code')).toHaveCount(2);
  await expect(page.getByRole('region', { name: 'Question results', exact: true }).getByText('The cited policy supports the prohibition.')).toHaveCount(8);
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
    rows: [evaluationRow],
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
  await page.getByRole('region', { name: 'Question results', exact: true }).getByText('Can I paste customer data into public AI?', { exact: false }).click();
  await expect(page.getByRole('region', { name: 'Question results', exact: true }).locator('.answer-text code')).toHaveCount(1);
});


test('expands metric questions and judge details with keyboard controls without starting a run', async ({ page }) => {
  let starts = 0;
  const rows = Array.from({ length: 5 }, (_, index) => ({
    ...evaluationRow, case_id: `case-${index}`, question: `Policy question ${index + 1}?`, level: index + 1,
    metrics: { ...evaluationRow.metrics, faithfulness: index === 3
      ? { status: 'error', value: null, reason: 'Provider timed out.' }
      : index === 4 ? { status: 'not_applicable', value: null, reason: 'No retrieved context.' }
      : { status: 'scored', value: 0.8, reason: '' } },
  }));
  const run = { ...evaluationRun, configuration: { ...evaluationRun.configuration, presets: { standard: 4 } }, rows };
  await page.route('**/api/evaluations**', route => {
    if (route.request().method() === 'POST') starts++;
    const path = new URL(route.request().url()).pathname;
    return route.fulfill({ json: path === '/api/evaluations' ? evaluationMetadata : path === '/api/evaluations/runs' ? [run] : run });
  });
  await page.goto('/evaluations');
  await expect(page.getByText('completed · 36/36 answer attempts processed')).toBeVisible();
  for (const name of ['Faithfulness', 'Context precision', 'Context recall', 'Answer relevancy', 'Factual correctness']) {
    const card = page.getByRole('region', { name, exact: true });
    const toggle = card.getByText('Question breakdown · 5 questions', { exact: true });
    await expect(card.getByText('1. Policy question 1?', { exact: true })).toBeHidden();
    await toggle.focus();
    await page.keyboard.press('Enter');
    await expect(card.getByText('5. Policy question 5?', { exact: true })).toBeVisible();
    if (name === 'Faithfulness') {
      await expect(card.getByText('Evaluation error', { exact: true })).toBeVisible();
      await expect(card.getByText('Not applicable', { exact: true })).toBeVisible();
      await card.getByText('View answer and evidence', { exact: true }).first().click();
      await expect(card.locator('.answer-text code').first()).toBeVisible();
      await page.setViewportSize({ width: 320, height: 900 });
      expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
    }
    await toggle.focus();
    await page.keyboard.press('Enter');
    await expect(card.getByText('1. Policy question 1?', { exact: true })).toBeHidden();
  }
  await page.getByText('Criterion and question results', { exact: true }).first().click();
  await expect(page.getByRole('region', { name: 'LLM judge — automated assessment', exact: true }).getByText('Policy question 1?', { exact: true }).first()).toBeVisible();
  expect(starts).toBe(0);
});
