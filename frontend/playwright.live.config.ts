import { defineConfig } from '@playwright/test';

export default defineConfig({
  testDir: './live', workers: 1, retries: 0, timeout: 60000,
  use: { baseURL: 'http://127.0.0.1:8001', viewport: { width: 1572, height: 1000 }, colorScheme: 'light' },
});
