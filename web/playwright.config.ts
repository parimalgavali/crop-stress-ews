import { defineConfig, devices } from '@playwright/test'

export default defineConfig({
  testDir: './e2e',
  use: { baseURL: 'http://localhost:4173', ...devices['Desktop Chrome'] },
  webServer: { command: 'npm run build && npm run preview -- --port 4173', port: 4173 },
})
