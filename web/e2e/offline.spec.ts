import { expect, test } from '@playwright/test'

// ADR 0024: after one online visit the app opens without internet, from the service worker cache.
test.beforeEach(async ({ page }) => {
  await page.addInitScript(() => localStorage.setItem('cropews-intro-seen', '1'))
})

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

test('a prepared visit pack reopens offline, records a visit and keeps it when the pack is removed', async ({ page, context }) => {
  let offline = false;
  await context.route('https://tile.openstreetmap.org/**', (r) => r.abort());
  await context.route('**/live/latest.json', (route) => offline ? route.abort() : route.fulfill({ json: {
    as_of: '2026-11-26', attribution: 'Test boundary source',
    fields: { type: 'FeatureCollection', features: [{ type: 'Feature', id: 'LWK-PACK', geometry: { type: 'Polygon', coordinates: [[[8, 51.5], [8.01, 51.5], [8.01, 51.51], [8, 51.5]]] }, properties: { field_id: 'LWK-PACK', district: 'Soest', area_ha: 4, declared_crop: 'unknown', level: null } }] },
    conditions: { 'LWK-PACK': { s2_date: '2026-11-24', s2_days_ago: 2 } },
  } }));
  await page.goto('/?field=LWK-PACK');
  await page.getByRole('button', { name: 'EN', exact: true }).click();
  const packs = page.getByRole('region', { name: 'Offline visits', exact: true });
  await packs.locator('summary').filter({ hasText: 'Choose fields for an offline pack' }).click();
  await packs.getByRole('checkbox', { name: /LWK-PACK/ }).check();
  await packs.getByRole('button', { name: 'Save selected visits' }).click();
  await expect(packs.getByRole('status')).toContainText('Pack saved.', { timeout: 25000 });
  const cachedUrls = await page.evaluate(async () => {
    const cache = await caches.open('cropews-v2');
    return (await cache.keys()).map((r) => r.url);
  });
  expect(cachedUrls.some((url) => url.endsWith('.js'))).toBe(true);
  expect(cachedUrls.every((url) => new URL(url).origin === 'http://localhost:4173')).toBe(true);
  offline = true;
  await context.setOffline(true);
  await page.goto('/');
  await page.getByRole('button', { name: 'EN', exact: true }).click();
  await page.getByRole('button', { name: 'Open saved pack' }).click();
  const visit = page.getByRole('region', { name: 'Your field visit: LWK-PACK' });
  await expect(visit).toContainText('2026-11-26');
  await expect(visit).toContainText('2026-11-24');
  await expect(visit).toContainText('does not mean low risk');
  await expect(visit).toContainText('does not update itself');
  await visit.getByRole('button', { name: 'Record what you saw' }).click();
  await visit.getByLabel('What did you see?').selectOption('standing_water');
  await visit.getByRole('button', { name: 'Save record' }).click();
  await expect(visit.getByRole('status').filter({ hasText: 'Saved: visit on' })).toBeVisible();
  await visit.getByText('Saved field boundary (outline only; no street map)').click();
  await expect(visit.getByRole('img')).toBeVisible();
  await page.getByRole('button', { name: 'Remove this pack' }).click();
  await expect(page.getByRole('button', { name: 'Open saved pack' })).toHaveCount(0);
  const records = await page.evaluate(() => JSON.parse(localStorage.getItem('cropews.observations.v1') ?? '[]'));
  expect(records).toHaveLength(1);
  expect(records[0]).toMatchObject({ field_id: 'LWK-PACK', symptom: 'standing_water', review_status: 'unreviewed' });
});

test('a failed app download never claims an offline pack was saved', async ({ page, context }) => {
  await context.route('https://tile.openstreetmap.org/**', (r) => r.abort());
  await context.route('**/live/latest.json', (r) => r.fulfill({ json: {
    as_of: '2026-11-26', attribution: 'test', conditions: {},
    fields: { type: 'FeatureCollection', features: [{ type: 'Feature', id: 'LWK-FAIL', geometry: { type: 'Polygon', coordinates: [[[8, 51.5], [8.01, 51.5], [8.01, 51.51], [8, 51.5]]] }, properties: { field_id: 'LWK-FAIL', district: 'Soest', area_ha: 4, declared_crop: 'unknown', level: null } }] },
  } }));
  await page.goto('/?field=LWK-FAIL');
  await page.getByRole('button', { name: 'EN', exact: true }).click();
  await page.evaluate(async () => { await navigator.serviceWorker.ready; });
  await context.setOffline(true);
  // Simulate a required stylesheet that has never been downloaded.
  await page.evaluate(() => {
    const link = document.createElement('link'); link.rel = 'stylesheet';
    link.href = '/assets/not-downloaded.css'; document.head.append(link);
  });
  const packs = page.getByRole('region', { name: 'Offline visits', exact: true });
  await packs.locator('summary').filter({ hasText: 'Choose fields for an offline pack' }).click();
  await packs.getByRole('checkbox').check();
  await packs.getByRole('button', { name: 'Save selected visits' }).click();
  await expect(packs.getByRole('alert')).toContainText('App download failed', { timeout: 25000 });
  expect(await page.evaluate(() => localStorage.getItem('cropews.visit-packs.v1'))).toBeNull();
});
