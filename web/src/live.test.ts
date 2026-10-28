import { describe, expect, it } from 'vitest'
import { conditionLines, greenness, radarChanged, LIVE_STRINGS, scoreLine, trend } from './live'

describe('live conditions', () => {
  it('maps numbers to plain words', () => {
    expect(greenness(0.2)).toBe('bare')
    expect(greenness(0.7)).toBe('green')
    expect(trend(0.1)).toBe('up')
    expect(trend(null)).toBeNull()
    expect(radarChanged(-2.5)).toBe(true)
  })

  it('builds lines and handles missing optical data and frost', () => {
    const lines = conditionLines(
      { s1_days_ago: 1, vv_change_db: 0.3, rain_30d_mm: 61.4, tmean_7d_c: 4, tmin_7d_c: -2 },
      'Mais',
      'en',
    ).map((l) => l.text)
    expect(lines[0]).toBe('No clear satellite image recently (clouds)')
    expect(lines).toContain('Rain in the last 30 days: 61 mm')
    expect(lines.some((t) => t.endsWith('Frost'))).toBe(true)
    expect(lines.at(-1)).toBe('Crop declared this year: Mais')
  })

  it('shows the winter-wheat guess with how sure it is', () => {
    const yes = conditionLines({}, '', 'en', 0.83).map((l) => l.text)
    expect(yes).toContain('Probably winter wheat (83% sure, satellite guess)')
    const no = conditionLines({}, '', 'de', 0.1).map((l) => l.text)
    expect(no.some((t) => t.startsWith('Wahrscheinlich kein Winterweizen (zu 90 %'))).toBe(true)
  })
})

describe('forecast line', () => {
  const fc = { fc_to: '2026-11-02', fc_rain_5d_mm: 24.4, fc_tmin_5d_c: -2.2, fc_frost_days: 1 }
  it('says rain, lowest temperature, heavy rain and frost in English', () => {
    const text = conditionLines({}, 'Winterweichweizen', 'en', null, fc).map((l) => l.text)
    expect(text).toContain(
      'Next 5 days (weather forecast): 24 mm rain, lowest -2 °C · heavy rain expected · frost on 1 night',
    )
  })
  it('says it in German and omits notes when calm', () => {
    const calm = { ...fc, fc_rain_5d_mm: 3, fc_tmin_5d_c: 4, fc_frost_days: 0 }
    const text = conditionLines({}, 'Winterweichweizen', 'de', null, calm).map((l) => l.text)
    expect(text).toContain('Nächste 5 Tage (Wettervorhersage): 3 mm Regen, tiefstens 4 °C')
  })
})

describe('scoreLine', () => {
  const h = { issued: 300, pending: 50, scored: 250, onsets: 8, auroc: 0.8, red_hits: 5, red_false: 30, missed: 3 }
  it('says nothing is checked before the first scored forecast', () => {
    expect(scoreLine(null, 'en')).toMatch(/none checked yet/)
    expect(scoreLine({ as_of: '2027-04-06', horizons: { '14': null } }, 'de')).toMatch(/noch keine/)
  })
  it('reports hits out of onsets', () => {
    expect(scoreLine({ as_of: '2027-05-01', horizons: { '14': h } }, 'en')).toBe(
      'Forecast check: 250 forecasts checked so far. A red alarm came before 5 of 8 stress events (14 days ahead).',
    )
  })
})

describe('alert text', () => {
  it('exists in both languages', () => {
    expect(LIVE_STRINGS.en.alert).toMatch(/red/)
    expect(LIVE_STRINGS.de.alert).toMatch(/rot/)
  })
})
