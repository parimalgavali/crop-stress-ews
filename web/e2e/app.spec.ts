import { expect, test } from '@playwright/test'

const DATES = ['2024-05-05', '2024-05-10']

test.beforeEach(async ({ page }, testInfo) => {
  if (!testInfo.title.includes('intro'))
    await page.addInitScript(() => localStorage.setItem('cropews-intro-seen', '1'))
})
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
      // utterances are chained via onend; fire it so the whole queue is captured
      queueMicrotask(() => u.onend?.(new Event('end') as never))
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
  expect(spoken[0]).toMatch(/^en-GB\|Field f2, Soest\./)
  expect(spoken.join(' ')).toContain('Next 7 days: Low risk')

  await page.getByRole('slider').fill('1')
  await expect(page.getByTestId('current-date')).toHaveText('10 May')
  await expect(page.getByTestId('horizon-21')).toContainText('High risk')

  await page.getByRole('group', { name: /Language|Sprache/ }).getByRole('button', { name: 'DE' }).click()
  await expect(page.getByTestId('horizon-21')).toContainText('Hohes Risiko')
})

test('keyboard only: tab to the field list and the read-aloud button', async ({ page }) => {
  await page.goto('/')
  await page.getByRole('group', { name: /Language|Sprache/ }).getByRole('button', { name: 'EN' }).click()
  const select = page.getByLabel('Field', { exact: true })
  await expect(select.locator('option')).toHaveCount(3)
  await select.focus()
  // Native type-ahead selects the first Field option without an OS popup.
  await page.keyboard.press('f')
  await expect(page.getByTestId('horizon-7')).toBeVisible()
  await page.keyboard.press('Tab')
  await expect(page.getByRole('button', { name: /Listen/ })).toBeFocused()
})

test('live mode shows current conditions in plain words', async ({ page }) => {
  // Pin today near as_of so the stale-data notice (older than 7 days) doesn't appear.
  await page.clock.setFixedTime(new Date('2026-11-02T10:00:00'))
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
  await expect(page.getByRole('img', { name: /Comparison unavailable: contributing-field count is unknown/ })).toBeVisible()
  await page.route('https://planetarycomputer.microsoft.com/api/stac/v1/search', (r) =>
    r.fulfill({ json: { type: 'FeatureCollection', features: [] } }),
  )
  await page.getByRole('button', { name: /Show satellite photo/ }).click()
  await expect(page.getByRole('alert')).toHaveText('No satellite photo found for this date.')
  await page.getByRole('button', { name: /Looks fine/ }).click()
  await expect(page.getByRole('status').filter({ hasText: 'You checked it on' })).toContainText('You checked it on')
  await page.reload()
  await page.getByRole('group', { name: /Language|Sprache/ }).getByRole('button', { name: 'EN' }).click()
  await page.getByRole('button', { name: 'Live' }).click()
  await page.getByLabel('Field', { exact: true }).selectOption('LWK-1')
  await expect(page.getByRole('status').filter({ hasText: 'You checked it on' })).toContainText('looks fine')
  await page.getByRole('button', { name: /Listen/ }).click()
  const spoken = await page.evaluate(() => (window as unknown as { spoken: string[] }).spoken)
  const spokenText = spoken.map((x) => x.replace(/^[^|]+\|/, '')).join(' ')
  expect(spokenText).toMatch(/^Field LWK-1, Soest\./)
  expect(spokenText).toContain('Last clear satellite image')
  expect(spokenText).toContain('No forecast is available')
  expect(spokenText).toMatch(/You checked it on .*: looks fine\./)
  expect(spokenText).toContain('Greenness since 1 October: from 0.50 to 0.70')
  await page.getByRole('button', { name: 'Start a field visit' }).click()
  await expect(page.getByRole('heading', { name: 'Your field visit' })).toBeVisible()
  await expect(page.getByText('No forecast is available. This does not mean low risk.', { exact: true })).toBeVisible()
  await expect(page.getByTestId('live-lines')).not.toBeVisible()
  await page.getByRole('button', { name: 'Record what you saw' }).click()
  await page.getByLabel('What did you see?').selectOption('standing_water')
  await page.getByRole('button', { name: 'Save record' }).click()
  await expect(page.getByRole('status').filter({ hasText: 'Saved: visit on' })).toBeVisible()
  await page.getByRole('button', { name: /Listen/ }).click()
  await expect.poll(async () => page.evaluate(() => (window as unknown as { spoken: string[] }).spoken.join(' '))).toContain('These are inspection prompts')
  await page.getByRole('button', { name: 'Return to full Live view' }).click()
  await expect(page.getByTestId('live-lines')).toBeVisible()

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
  await page.locator('details.more > summary').click()
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

test('live mode: print stylesheet shows a one-page field report', async ({ page }) => {
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
  await page.goto('/')
  await page.getByRole('group', { name: /Language|Sprache/ }).getByRole('button', { name: 'EN' }).click()
  await page.getByRole('button', { name: 'Live' }).click()
  await page.getByLabel('Field', { exact: true }).selectOption('LWK-1')
  await page.locator('details.more > summary').click()
  await expect(page.getByRole('button', { name: /Print this card/ })).toBeVisible()
  await page.emulateMedia({ media: 'print' })
  await expect(page.getByTestId('print-report')).toBeVisible()
  await expect(page.getByTestId('print-report')).toContainText('?field=LWK-1')
  await expect(page.getByRole('button', { name: /Print this card/ })).toBeHidden()
  await page.emulateMedia({ media: 'screen' })
})

test('intro: shown once, reopened with ?', async ({ page }) => {
  await page.goto('/')
  await expect(page.getByRole('dialog', { name: 'How it works' })).toBeVisible()
  await page.getByRole('button', { name: 'Got it' }).click()
  await expect(page.getByRole('dialog')).toBeHidden()
  await page.reload()
  await expect(page.getByRole('dialog')).toHaveCount(0)
  await page.getByRole('button', { name: 'How it works' }).click()
  await expect(page.getByRole('dialog', { name: 'How it works' })).toBeVisible()
})

test('no basemap toggle is shown (ADR 0048 removal)', async ({ page }) => {
  await page.goto('/')
  await expect(page.locator('.basemap-toggle')).toHaveCount(0)
})

test('saved Live fields keep their names after reload and reopen the original field', async ({ page }) => {
  await page.route('**/live/latest.json', (r) => r.fulfill({ json: {
    as_of: '2026-11-26', attribution: 'test',
    fields: { ...fields, features: fields.features.map((f) => ({ ...f, properties: { ...f.properties, declared_crop: 'wheat' } })) },
    conditions: { f1: {}, f2: {} },
  } }))
  await page.goto('/?field=f2')
  await page.getByRole('group', { name: /Language|Sprache/ }).getByRole('button', { name: 'EN' }).click()
  const mine = page.getByRole('region', { name: 'My fields', exact: true })
  await mine.getByLabel('Name for this field').fill('Behind the barn')
  await mine.getByRole('button', { name: 'Save field name' }).click()
  await expect(mine.getByRole('status')).toContainText('Saved on this device')
  const downloaded = page.waitForEvent('download')
  await page.getByRole('button', { name: 'Download my backup' }).click()
  const file = await downloaded
  expect(file.suggestedFilename()).toMatch(/^crop-ews-backup-.*\.json$/)
  const { readFile } = await import('node:fs/promises')
  const backup = JSON.parse(await readFile((await file.path())!, 'utf8'))
  expect(backup.schema_version).toBe(1)
  expect(backup.saved_fields[0]).toMatchObject({ field_id: 'f2', name: 'Behind the barn' })
  await page.reload()
  await expect(mine.getByRole('button', { name: 'Behind the barn', exact: true })).toBeVisible()
  await page.getByLabel('Field', { exact: true }).selectOption('f1')
  await mine.getByRole('button', { name: 'Behind the barn', exact: true }).click()
  await expect(page.getByLabel('Field', { exact: true })).toHaveValue('f2')
  await expect(mine).toContainText('No forecast available')
  await mine.getByRole('button', { name: 'Remove: Behind the barn' }).click()
  await expect(mine).toContainText('No saved fields yet')
  await page.getByLabel('Choose a backup file').setInputFiles((await file.path())!)
  await expect(page.getByRole('button', { name: 'Restore this backup' })).toBeVisible()
  await page.getByLabel('Replace existing work', { exact: true }).check()
  await expect(page.getByRole('button', { name: 'Restore this backup' })).toBeDisabled()
  await page.getByLabel('I understand this replaces my saved fields, checks and visit records.').check()
  await page.getByRole('button', { name: 'Restore this backup' }).click()
  await expect(mine.getByRole('button', { name: 'Behind the barn', exact: true })).toBeVisible()
  await page.reload()
  await expect(mine.getByRole('button', { name: 'Behind the barn', exact: true })).toBeVisible()
})


test('intro keyboard focus stays inside help and returns to its opener', async ({ page }) => {
  await page.goto('/')
  const dialog = page.getByRole('dialog')
  const close = dialog.getByRole('button')
  await expect(close).toBeFocused()
  await page.keyboard.press('Tab')
  await expect(close).toBeFocused()
  await page.keyboard.press('Shift+Tab')
  await expect(close).toBeFocused()
  await page.keyboard.press('Enter')
  await expect(dialog).not.toBeVisible()
  const help = page.getByRole('button', { name: /How it works|So funktioniert es/, exact: true })
  await help.focus(); await page.keyboard.press('Enter')
  await expect(dialog).toBeVisible()
  await page.keyboard.press('Escape')
  await expect(help).toBeFocused()
})

test('keyboard visits can read a Live card, open details and save a visit', async ({ page }) => {
  await page.route('**/live/latest.json', (r) => r.fulfill({ json: {
    as_of: '2026-11-26', attribution: 'test', fields: { ...fields, features: fields.features.map((f) => ({ ...f, properties: { ...f.properties, declared_crop: 'wheat' } })) },
    conditions: { f1: {}, f2: {} },
  } }))
  await page.goto('/?field=f2')
  await page.getByRole('button', { name: /Listen/ }).focus()
  await page.keyboard.press('Enter')
  await expect.poll(() => page.evaluate(() => (window as unknown as { spoken: string[] }).spoken.length)).toBeGreaterThan(0)
  await page.locator('details.more > summary').focus(); await page.keyboard.press('Enter')
  await page.getByText('📝 Field visit record', { exact: true }).focus(); await page.keyboard.press('Enter')
  await page.getByRole('button', { name: 'Record what you saw' }).focus(); await page.keyboard.press('Enter')
  await page.getByRole('button', { name: 'Save record', exact: true }).focus(); await page.keyboard.press('Enter')
  await expect(page.getByText(/Saved: visit on/)).toBeVisible()
})

for (const lang of ['EN', 'DE']) {
  test(`${lang}: small phone and enlarged text keep controls reachable without horizontal scrolling`, async ({ page }) => {
    await page.setViewportSize({ width: 320, height: 640 })
    await page.route('**/live/latest.json', (r) => r.fulfill({ json: {
      as_of: '2026-11-26', attribution: 'test',
      fields: { ...fields, features: fields.features.map((f) => ({ ...f, properties: { ...f.properties, declared_crop: 'wheat' } })) },
      conditions: { f1: {}, f2: {} },
      forecast: { Soest: { fc_to: '2026-12-01', fc_rain_5d_mm: 20, fc_tmin_5d_c: -10, fc_frost_days: 2,
        fc_days: Array.from({ length: 5 }, (_, i) => ({ date: `2026-11-${26 + i}`, pr: 12, tmin: -10, tmax: 12 })) } },
    } }))
    await page.goto('/')
    await page.getByRole('group', { name: /Language|Sprache/ }).getByRole('button', { name: lang }).click()
    await page.addStyleTag({ content: ':root { font-size: 36px; }' })
    const select = page.locator('#field-select')
    await expect(select.locator('option')).toHaveCount(3)
    await select.selectOption('f2')
    const next = page.getByRole('button', { name: lang === 'EN' ? 'Next date' : 'Nächstes Datum', exact: true })
    await next.scrollIntoViewIfNeeded()
    await next.click()
    await expect(page.getByTestId('current-date')).toHaveText(lang === 'EN' ? '10 May' : '10. Mai')
    const overflow = await page.evaluate(() => [...document.querySelectorAll('body *')].filter((el) => { const b = el.getBoundingClientRect(); return b.width > 0 && b.right > innerWidth + 1 }).map((el) => `${el.tagName}.${el.className}`))
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth + 1), overflow.join(', ')).toBe(true)
    const listen = page.getByRole('button', { name: lang === 'EN' ? /Listen/ : /Vorlesen/ })
    await listen.scrollIntoViewIfNeeded()
    const box = await listen.boundingBox()
    expect(box!.height).toBeGreaterThanOrEqual(48)
    await listen.click()
    await page.getByRole('button', { name: lang === 'EN' ? 'How it works' : 'So funktioniert es', exact: true }).click()
    const close = page.getByRole('dialog').getByRole('button')
    await close.scrollIntoViewIfNeeded(); await close.click()
    await expect(page.getByRole('dialog')).not.toBeVisible()
    await page.getByRole('button', { name: lang === 'EN' ? 'Live' : 'Aktuell', exact: true }).click()
    await expect(select.locator('option')).toHaveCount(3)
    await select.selectOption('f2')
    const save = page.getByRole('button', { name: lang === 'EN' ? 'Save field name' : 'Feldname speichern' })
    await save.scrollIntoViewIfNeeded(); await save.click()
    const backup = page.getByRole('button', { name: lang === 'EN' ? 'Download my backup' : 'Meine Sicherung herunterladen' })
    await backup.scrollIntoViewIfNeeded()
    expect((await backup.boundingBox())!.height).toBeGreaterThanOrEqual(48)
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth + 1)).toBe(true)
  })
}

for (const lang of ['EN', 'DE']) {
  test(`${lang}: satellite explanations and one upper speaker stay consistent`, async ({ page }) => {
    await page.setViewportSize({ width: 320, height: 640 })
    await page.route('**/live/latest.json', (r) => r.fulfill({ json: {
      as_of: '2026-11-26', attribution: 'test',
      fields: { ...fields, features: fields.features.map((f) => ({ ...f, properties: { ...f.properties, declared_crop: 'wheat' } })) },
      conditions: { f2: { s2_date: '2026-11-24', s2_days_ago: 2, ndvi: 0.33 } },
      season: { fields: { f2: [['2026-10-05', 0.23], ['2026-11-24', 0.33]] }, peers: { Soest: [['2026-10-05', 0.4], ['2026-11-24', 0.5]] }, peer_kind: 'all',
        peer_support: { Soest: { '2026-11-24': { count: 5, previous_count: 6, retained_from_previous: 4 } } } },
      subfield: { f2: { date: '2026-11-24', assessment: { status: 'insufficient', usable_pixels: 2, clear_fraction: 0.1 }, zones: [],
        quality: { clear: 0.1, cloud_shadow: 0.9, unstable: true, interior_px: 20 },
        grid: { h: 1, w: 2, ndvi: [[0.33, null]], zone_cells: [] } } },
    } }))
    await page.goto('/?field=f2')
    await page.getByRole('group', { name: /Language|Sprache/ }).getByRole('button', { name: lang }).click()
    const chart = page.getByTestId('season-chart')
    await expect(chart).toContainText(lang === 'EN' ? 'Mixed monitored crops · Soest' : 'Gemischte beobachtete Kulturen · Soest')
    await expect(chart).toContainText(lang === 'EN' ? '5 contributing fields' : '5 beitragende Felder')
    await expect(chart).toContainText(lang === 'EN' ? 'Contributing fields changed' : 'tragen andere Felder bei')
    const patch = page.getByRole('img', { name: lang === 'EN' ? /Not enough clear detail/ : /Nicht genug klare Bilddetails/ })
    await expect(patch).toBeVisible()
    await expect(page.locator('.upper-read-button')).toHaveCount(1)
    await expect(page.locator('.card .speak')).toHaveCount(0)
    await patch.scrollIntoViewIfNeeded()
    expect((await page.locator('.upper-read-button').boundingBox())!.y).toBeLessThan(20)
    await page.locator('.upper-read-button').click()
    await expect.poll(async () => (await page.evaluate(() => (window as unknown as { spoken: string[] }).spoken)).join(' ')).toContain(lang === 'EN' ? 'Not enough clear detail' : 'Nicht genug klare Bilddetails')
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth + 1)).toBe(true)
  })
}
