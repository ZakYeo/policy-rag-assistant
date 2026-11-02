// Decode, play and seek the recorded video with Playwright; make an inline GIF preview.
import { chromium, expect } from '@playwright/test';
import { createServer } from 'node:http';
import { createReadStream } from 'node:fs';
import { mkdtemp, readFile, rm, stat, writeFile } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { fileURLToPath } from 'node:url';
import { execFileSync } from 'node:child_process';

const media = fileURLToPath(new URL('../../docs/media/', import.meta.url));
const videoPath = join(media, 'live-question-demo.webm');
const { size } = await stat(videoPath);
const server = createServer((request, response) => {
  if (request.url !== '/demo.webm') {
    response.writeHead(200, { 'Content-Type': 'text/html' });
    response.end('<!doctype html><video controls muted src="/demo.webm"></video>');
    return;
  }
  const range = /^bytes=(\d+)-(\d*)$/.exec(request.headers.range ?? '');
  const start = range ? Number(range[1]) : 0;
  const end = range?.[2] ? Math.min(Number(range[2]), size - 1) : size - 1;
  if (start > end || start >= size) { response.writeHead(416); response.end(); return; }
  const headers = { 'Content-Type': 'video/webm', 'Accept-Ranges': 'bytes', 'Content-Length': end - start + 1 };
  if (range) headers['Content-Range'] = `bytes ${start}-${end}/${size}`;
  response.writeHead(range ? 206 : 200, headers);
  createReadStream(videoPath, { start, end }).pipe(response);
});
await new Promise((resolve) => server.listen(0, '127.0.0.1', resolve));
const frames = await mkdtemp(join(tmpdir(), 'northstar-demo-'));
const browser = await chromium.launch({ headless: true });
try {
  const page = await browser.newPage();
  await page.goto(`http://127.0.0.1:${server.address().port}`);
  await page.waitForFunction(() => document.querySelector('video').readyState >= 2);
  const metadata = await page.locator('video').evaluate((video) => ({ duration: video.duration, width: video.videoWidth, height: video.videoHeight }));
  expect(metadata.duration).toBeGreaterThan(10);
  expect(metadata.width).toBe(1440);
  expect(metadata.height).toBe(1000);
  await page.locator('video').evaluate((video) => video.play());
  await page.waitForFunction(() => document.querySelector('video').currentTime > 0.25);
  async function frame(time, width) {
    return page.locator('video').evaluate(async (video, { time, width }) => {
      video.pause();
      await new Promise((resolve, reject) => {
        video.onseeked = () => { video.onseeked = null; video.onerror = null; resolve(); };
        video.onerror = () => { video.onseeked = null; video.onerror = null; reject(new Error('Video seeking failed.')); };
        video.currentTime = time;
      });
      const canvas = document.createElement('canvas');
      canvas.width = width;
      canvas.height = Math.round(width * video.videoHeight / video.videoWidth);
      canvas.getContext('2d').drawImage(video, 0, 0, canvas.width, canvas.height);
      return canvas.toDataURL('image/png').split(',')[1];
    }, { time, width });
  }
  await writeFile(join(media, 'live-demo-poster.png'), Buffer.from(await frame(metadata.duration - 0.2, 1440), 'base64'));
  for (let index = 0; index < Math.ceil(metadata.duration * 4); index++) {
    const png = await frame(Math.min(index / 4 + 0.01, metadata.duration - 0.1), 960);
    await writeFile(join(frames, `${String(index).padStart(4, '0')}.png`), Buffer.from(png, 'base64'));
  }
  execFileSync(fileURLToPath(new URL('../../.venv/bin/python', import.meta.url)), ['-c', `
from pathlib import Path
from PIL import Image
import sys
frames = [Image.open(path).convert('P', palette=Image.Palette.ADAPTIVE, colors=128) for path in sorted(Path(sys.argv[1]).glob('*.png'))]
frames[0].save(sys.argv[2], save_all=True, append_images=frames[1:], duration=250, loop=0, optimize=True)
`, frames, join(media, 'live-question-preview.gif')]);
  const summaryPath = join(media, 'capture-summary.json');
  const summary = JSON.parse(await readFile(summaryPath, 'utf8'));
  await writeFile(summaryPath, JSON.stringify({ ...summary, playbackVerified: true, videoDurationSeconds: metadata.duration, videoSize: `${metadata.width}×${metadata.height}` }, null, 2) + '\n');
  console.log(JSON.stringify({ playbackVerified: true, ...metadata, preview: 'live-question-preview.gif' }));
} finally {
  await browser.close();
  await new Promise((resolve) => server.close(resolve));
  await rm(frames, { recursive: true, force: true });
}
