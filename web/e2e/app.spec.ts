import { expect, test } from '@playwright/test'

const DATES = ['2024-05-05', '2024-05-10']
const square = (x: number) => ({
  type: 'Polygon',
  coordinates: [[[x, 51.5], [x + 0.01, 51.5], [x + 0.01, 51.51], [x, 51.51], [x, 51.5]]],
})
const fields = {
  type: 'FeatureCollection',
  features: [
    { type: 'Feature', id: 'f1', geometry: square(8.0), properties: { field_id: 'f1', district: 'Soest', area_ha: 3.2, level: 'green' } },
    { type: 'Feature', id: 'f2', geometry: square(8.1), properties: { field_id: 'f2', district: 'Soest', area_ha: 5.0, level: 'red' } },
  ],
}
const reasons = [{ code: 'behind_neighbours', text_en: 'Crop is behind neighbouring fields', text_de: 'Bestand liegt hinter den Nachbarfeldern' }]
const risk = (date: string) => ({
  field_id: 'f2',
  year: 2024,
  date,
  district: 'Soest',
  horizons: [
    { days: 7, risk: 0.03, level: 'green', reasons },
    { days: 14, risk: 0.07, level: 'amber', reasons },
    { days: 21, risk: date === DATES[1] ? 0.3 : 0.05, level: date === DATES[1] ? 'red' : 'green', reasons },
  ],
})

test.beforeEach(async ({ page }) => {
  await page.route('https://tile.openstreetmap.org/**', (r) => r.abort())
  await page.route('**/api/dates?*', (r) => r.fulfill({ json: DATES }))
  await page.route('**/api/fields?*', (r) => r.fulfill({ json: fields }))
  await page.route('**/api/fields/*/risk?*', (r) => {
    const date = new URL(r.request().url()).searchParams.get('date') ?? DATES[0]
    return r.fulfill({ json: risk(date) })
  })
  await page.addInitScript(() => {
    ;(window as unknown as { spoken: string[] }).spoken = []
    window.speechSynthesis.speak = (u: SpeechSynthesisUtterance) => {
      ;(window as unknown as { spoken: string[] }).spoken.push(`${u.lang}|${u.text}`)
    }
  })
})

test('choose a field, see three traffic lights, hear it, step the season', async ({ page }) => {
  await page.goto('/')
  await page.getByRole('group', { name: /Language|Sprache/ }).getByRole('button', { name: 'EN' }).click()
  await expect(page.locator('.map canvas')).toBeVisible()

  const select = page.getByLabel('Field', { exact: true })
  await expect(select.locator('option')).toHaveCount(3)
  await expect(select.locator('option').nth(1)).toContainText('High risk') // worst first
  await select.selectOption('f2')

  await expect(page.getByTestId('horizon-7')).toContainText('Low risk')
  await expect(page.getByTestId('horizon-14')).toContainText('Crop is behind neighbouring fields')
  await expect(page.getByTestId('horizon-21')).toContainText('Low risk')

  await page.getByRole('button', { name: /Listen/ }).click()
  const spoken = await page.evaluate(() => (window as unknown as { spoken: string[] }).spoken)
  expect(spoken[0]).toMatch(/^en-GB\|Field, Soest\. Next 7 days: Low risk/)

  await page.getByRole('slider').fill('1')
  await expect(page.getByTestId('current-date')).toHaveText('10 May')
  await expect(page.getByTestId('horizon-21')).toContainText('High risk')

  await page.getByRole('group', { name: /Language|Sprache/ }).getByRole('button', { name: 'DE' }).click()
  await expect(page.getByTestId('horizon-21')).toContainText('Hohes Risiko')
})

test('keyboard only: tab to the field list and the read-aloud button', async ({ page }) => {
  await page.goto('/')
  await page.getByRole('group', { name: /Language|Sprache/ }).getByRole('button', { name: 'EN' }).click()
  await page.getByLabel('Field', { exact: true }).focus()
  await page.keyboard.press('ArrowDown')
  await page.keyboard.press('ArrowDown')
  await expect(page.getByTestId('horizon-7')).toBeVisible()
  await page.keyboard.press('Tab')
  await expect(page.getByRole('button', { name: /Listen/ })).toBeFocused()
})

test('live mode shows current conditions in plain words', async ({ page }) => {
  await page.route('**/live/latest.json', (r) =>
    r.fulfill({
      json: {
        as_of: '2026-11-01',
        attribution: 'test',
        fields: {
          type: 'FeatureCollection',
          features: [
            { type: 'Feature', id: 'LWK-1', geometry: square(8.0), properties: { field_id: 'LWK-1', district: 'Soest', area_ha: 4, declared_crop: 'Mais', level: null } },
          ],
        },
        conditions: {
          'LWK-1': { s2_date: '2026-10-28', s2_days_ago: 4, ndvi: 0.7, ndvi_change: 0.2, s1_days_ago: 1, vv_change_db: 0.1, rain_30d_mm: 55, tmean_7d_c: 6, tmin_7d_c: 1 },
        },
        season: {
          fields: { 'LWK-1': [['2026-10-08', 0.5], ['2026-10-28', 0.7]] },
          peers: { Soest: [['2026-10-08', 0.45], ['2026-10-28', 0.5]] },
          peer_kind: 'all',
        },
      },
    }),
  )
  await page.goto('/')
  await page.getByRole('group', { name: /Language|Sprache/ }).getByRole('button', { name: 'EN' }).click()
  await page.getByRole('button', { name: 'Live' }).click()
  await expect(page.getByTestId('live-date')).toHaveText('1 November')
  await page.getByLabel('Field', { exact: true }).selectOption('LWK-1')
  const lines = page.getByTestId('live-lines')
  await expect(lines).toContainText('Last clear satellite image: 4 days ago')
  await expect(lines).toContainText('Green crop cover, getting greener')
  await expect(lines).toContainText('Rain in the last 30 days: 55 mm')
  await expect(page.getByRole('img', { name: /greener than the neighbours/ })).toBeVisible()
  await page.route('https://planetarycomputer.microsoft.com/api/stac/v1/search', (r) =>
    r.fulfill({ json: { type: 'FeatureCollection', features: [] } }),
  )
  await page.getByRole('button', { name: /Show satellite photo/ }).click()
  await expect(page.getByRole('alert')).toHaveText('No satellite photo found for this date.')
  await page.getByRole('button', { name: /Looks fine/ }).click()
  await expect(page.getByRole('status')).toContainText('You checked it on')
  await page.reload()
  await page.getByRole('group', { name: /Language|Sprache/ }).getByRole('button', { name: 'EN' }).click()
  await page.getByRole('button', { name: 'Live' }).click()
  await page.getByLabel('Field', { exact: true }).selectOption('LWK-1')
  await expect(page.getByRole('status')).toContainText('looks fine')
  await page.getByRole('button', { name: /Listen/ }).click()
  const spoken = await page.evaluate(() => (window as unknown as { spoken: string[] }).spoken)
  expect(spoken.at(-1)).toMatch(/^en-GB\|Field, Soest\. Last clear satellite image/)
  expect(spoken.at(-1)).toMatch(/You checked it on .*: looks fine\.$/)
  expect(spoken.at(-1)).toContain('Greenness since 1 October: from 0.50 to 0.70')
})

test('check my field: draw corners, then read satellite data for that polygon', async ({ page }) => {
  await page.route('**/live/latest.json', (r) =>
    r.fulfill({ json: { as_of: '2026-11-01', attribution: 'test', fields: { type: 'FeatureCollection', features: [] }, conditions: {} } }),
  )
  let searched: unknown = null
  await page.route('https://planetarycomputer.microsoft.com/api/stac/v1/search', (r) => {
    searched = r.request().postDataJSON()
    return r.fulfill({ json: { type: 'FeatureCollection', features: [] } })
  })
  await page.goto('/')
  await page.getByRole('group', { name: /Language|Sprache/ }).getByRole('button', { name: 'EN' }).click()
  await page.getByRole('button', { name: 'Live' }).click()
  await page.getByRole('button', { name: /Check my field/ }).click()
  const map = page.locator('.map')
  const box = (await map.boundingBox())!
  const [cx, cy] = [box.x + box.width / 2, box.y + box.height / 2]
  for (const [dx, dy] of [[0, 0], [60, 0], [0, 60]]) await page.mouse.click(cx + dx, cy + dy)
  await expect(page.getByTestId('corners')).toHaveText('Corners: 3')
  await page.getByRole('button', { name: /Done/ }).click()
  await expect(page.getByRole('alert')).toHaveText('No satellite images found for this field in the last 60 days.')
  expect((searched as { intersects: { type: string } }).intersects.type).toBe('Polygon')
})

test('a shared ?field= link opens the Live card and the address bar follows', async ({ page }) => {
  await page.route('**/live/latest.json', (r) =>
    r.fulfill({
      json: {
        as_of: '2026-11-01',
        attribution: 'test',
        fields: {
          type: 'FeatureCollection',
          features: [
            { type: 'Feature', id: 'LWK-1', geometry: square(8.0), properties: { field_id: 'LWK-1', district: 'Soest', area_ha: 4, declared_crop: 'Mais', level: null } },
          ],
        },
        conditions: {
          'LWK-1': { s2_date: '2026-10-28', s2_days_ago: 4, ndvi: 0.7, ndvi_change: 0.2, s1_days_ago: 1, vv_change_db: 0.1, rain_30d_mm: 55, tmean_7d_c: 6, tmin_7d_c: 1 },
        },
      },
    }),
  )
  await page.goto('/?field=LWK-1')
  await page.getByRole('group', { name: /Language|Sprache/ }).getByRole('button', { name: 'EN' }).click()
  await expect(page.getByLabel('Field', { exact: true })).toHaveValue('LWK-1')
  await expect(page.getByTestId('live-lines')).toContainText('Last clear satellite image')
  await expect(page.getByRole('button', { name: '🔗 Link to this field' })).toBeVisible()

  // Switching off Live clears the link target again
  await page.getByRole('button', { name: '2024' }).click()
  await expect(page).not.toHaveURL(/field=/)

  // Unknown field id: no crash, shows the "no data" hint
  await page.goto('/?field=DOES-NOT-EXIST')
  await page.getByRole('group', { name: /Language|Sprache/ }).getByRole('button', { name: 'EN' }).click()
  await expect(page.getByLabel('Field', { exact: true })).toHaveValue('')
  await expect(page.getByText('This field is not monitored.')).toBeVisible()
})

test('live mode: next/previous buttons walk the monitored fields', async ({ page }) => {
  const cond = { s2_date: '2026-10-28', s2_days_ago: 4, ndvi: 0.7, ndvi_change: 0.2, s1_days_ago: 1, vv_change_db: 0.1, rain_30d_mm: 55, tmean_7d_c: 6, tmin_7d_c: 1 }
  await page.route('**/live/latest.json', (r) =>
    r.fulfill({
      json: {
        as_of: '2026-11-01',
        attribution: 'test',
        fields: {
          type: 'FeatureCollection',
          features: [
            { type: 'Feature', id: 'LWK-1', geometry: square(8.0), properties: { field_id: 'LWK-1', district: 'Soest', area_ha: 4, declared_crop: 'Mais', level: null } },
            { type: 'Feature', id: 'LWK-2', geometry: square(8.2), properties: { field_id: 'LWK-2', district: 'Soest', area_ha: 3, declared_crop: 'Mais', level: null } },
          ],
        },
        conditions: { 'LWK-1': cond, 'LWK-2': cond },
      },
    }),
  )
  await page.goto('/')
  await page.getByRole('group', { name: /Language|Sprache/ }).getByRole('button', { name: 'EN' }).click()
  await page.getByRole('button', { name: 'Live' }).click()
  const select = page.getByLabel('Field', { exact: true })
  const next = page.getByRole('button', { name: /Next field/ })
  const prev = page.getByRole('button', { name: /Previous field/ })
  await expect(prev).toBeDisabled()
  await next.click()
  await expect(select).toHaveValue('LWK-1')
  await next.click()
  await expect(select).toHaveValue('LWK-2')
  await expect(next).toBeDisabled()
  await prev.click()
  await expect(select).toHaveValue('LWK-1')
})
