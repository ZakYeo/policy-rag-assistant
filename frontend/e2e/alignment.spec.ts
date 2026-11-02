import { expect, test } from '@playwright/test';

test('keeps shared page anchors aligned when navigating at different window shapes', async ({ page }, info) => {
  for (const [width, height] of [[1440, 1800], [1920, 1080], [1024, 900], [1023, 900], [960, 900], [768, 1024], [640, 900], [639, 900], [400, 844], [399, 844], [390, 844], [380, 844], [379, 844], [360, 780], [320, 720], [844, 390]]) {
    await page.setViewportSize({ width, height });
    await page.goto('/');
    await page.evaluate(() => document.fonts.ready);
    const measure = () => page.evaluate(() => {
      const bounds = (selector: string) => {
        const element = document.querySelector(selector)!;
        const box = element.getBoundingClientRect();
        return { x: box.x, y: box.y, width: box.width };
      };
      const title = document.querySelector('main h1')!;
      const description = title.parentElement!.querySelector(':scope > p')!;
      const box = description.getBoundingClientRect();
      return {
        header: bounds('header > div'), navigation: bounds('nav[aria-label="Main navigation"]'),
        title: bounds('main h1'), description: { x: box.x, y: box.y, width: box.width },
        card: bounds('main > section[aria-label="Ask a policy question"], main > form'),
      };
    });
    if (width === 390) await page.getByRole('button', { name: 'Switch to dark mode' }).click();
    const question = await measure();
    if (width === 1440 || width === 390) await page.screenshot({ path: info.outputPath(`ask-${width}.png`), fullPage: true });
    await page.getByRole('link', { name: 'Manage policies', exact: true }).click();
    await expect(page.getByRole('heading', { name: 'Manage policies', exact: true })).toBeVisible();
    const library = await measure();
    if (width === 1440 || width === 390) await page.screenshot({ path: info.outputPath(`library-${width}.png`), fullPage: true });
    for (const anchor of ['header', 'navigation', 'title', 'description', 'card'] as const) {
      for (const coordinate of ['x', 'y', 'width'] as const) {
        expect(Math.abs(question[anchor][coordinate] - library[anchor][coordinate]), `${width}×${height}: ${anchor}.${coordinate}`).toBeLessThan(0.5);
      }
    }
    await page.getByRole('link', { name: 'Ask policies', exact: true }).click();
    expect(await measure()).toEqual(question);
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
  }
});
