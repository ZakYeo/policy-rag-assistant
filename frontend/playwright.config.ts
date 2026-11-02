import { defineConfig } from '@playwright/test';

export default defineConfig({
  testDir: './e2e',
  fullyParallel: false,
  workers: 1,
  use: { baseURL: 'http://127.0.0.1:8010', trace: 'retain-on-failure' },
  reporter: [['list'], ['html', { open: 'never' }]],
  webServer: {
    command: '.venv/bin/python -m uvicorn browser_app:app --app-dir tests --host 127.0.0.1 --port 8010',
    cwd: '..', url: 'http://127.0.0.1:8010/health', reuseExistingServer: false,
    env: { ROUTER_PROVIDER: 'heuristic' },
  },
});
