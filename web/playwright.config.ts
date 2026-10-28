import { defineConfig, devices } from '@playwright/test'

export default defineConfig({
  testDir: './e2e',
  // The service worker would hide requests from page.route; the offline test allows it.
  use: { baseURL: 'http://localhost:4173', serviceWorkers: 'block', ...devices['Desktop Chrome'] },
  webServer: { command: 'npm run build && npm run preview -- --port 4173', port: 4173 },
})
