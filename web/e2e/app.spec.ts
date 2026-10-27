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
  await page.getByRole('button', { name: 'EN' }).click()
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

  await page.getByRole('button', { name: 'DE' }).click()
  await expect(page.getByTestId('horizon-21')).toContainText('Hohes Risiko')
})

test('keyboard only: tab to the field list and the read-aloud button', async ({ page }) => {
  await page.goto('/')
  await page.getByRole('button', { name: 'EN' }).click()
  await page.getByLabel('Field', { exact: true }).focus()
  await page.keyboard.press('ArrowDown')
  await page.keyboard.press('ArrowDown')
  await expect(page.getByTestId('horizon-7')).toBeVisible()
  await page.keyboard.press('Tab')
  await expect(page.getByRole('button', { name: /Listen/ })).toBeFocused()
})
