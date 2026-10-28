import { expect, test } from '@playwright/test'

// ADR 0024: after one online visit the app opens without internet, from the service worker cache.
test.use({ serviceWorkers: 'allow' })

test('opens offline after one visit and says so', async ({ page, context }) => {
  await context.route('https://tile.openstreetmap.org/**', (r) => r.abort())
  await page.goto('/')
  await page.evaluate(async () => {
    await navigator.serviceWorker.ready
    if (!navigator.serviceWorker.controller)
      await new Promise((r) => navigator.serviceWorker.addEventListener('controllerchange', r))
  })
  await page.reload()
  await context.setOffline(true)
  await page.reload()
  await expect(page.getByTestId('offline')).toBeVisible()
  await expect(page.getByRole('button', { name: /live/i })).toBeVisible()
  const manifest = await page.evaluate(() => document.querySelector('link[rel=manifest]')?.getAttribute('href'))
  expect(manifest).toBe('manifest.webmanifest')
})
