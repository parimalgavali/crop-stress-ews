import { describe, expect, it } from 'vitest'
import { conditionLines, greenness, radarChanged, LIVE_STRINGS, scoreLine, soilLine, staleNotice, trend } from './live'

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

  it('warns when live data is more than a week old', () => {
    const today = new Date(2026, 10, 10)
    expect(staleNotice('2026-11-05', 'en', today)).toBeNull()
    expect(staleNotice('2026-11-01', 'en', today)).toBe(
      'This data is 9 days old. The last update may have failed; it is retried every 5 days.',
    )
    expect(staleNotice('2026-11-01', 'de', today)).toMatch(/^Diese Daten sind 9 Tage alt/)
  })

  it('shows winter checks with a symbol and plain words', () => {
    const w = { emergence: 'behind' as const, z_ndvi: -2, n_clear: 3, radar_dates: 4, wet_date: '2026-12-02' }
    const lines = conditionLines({}, '', 'en', 0.8, undefined, w)
    expect(lines).toContainEqual({ icon: '⚠', text: LIVE_STRINGS.en.behind })
    expect(lines.some((l) => l.icon === '💧' && l.text.includes('standing water'))).toBe(true)
    const ok = conditionLines({}, '', 'de', 0.8, undefined, { ...w, emergence: 'ok', wet_date: null })
    expect(ok.map((l) => l.text)).toEqual(expect.arrayContaining([LIVE_STRINGS.de.emerged, LIVE_STRINGS.de.dry]))
  })

  it('shows the nearby DWD growth stage as observer evidence', () => {
    const p = { stage: 'emerged' as const, observers: 3, at_stage: 2, first_date: '2026-10-11', radius_km: 40 }
    const en = conditionLines({}, '', 'en', undefined, undefined, undefined, p)
    expect(en).toContainEqual({ icon: '🌿', text: 'Winter wheat around here: came up (2 of 3 DWD observers within 40 km, first on 11 October)' })
    const de = conditionLines({}, '', 'de', undefined, undefined, undefined, p)
    expect(de.at(-1)?.text).toMatch(/^Winterweizen in der Umgebung: aufgelaufen \(2 von 3 DWD-Beobachtern/)
  })

  it('describes the soil in plain words', () => {
    const soil = { soil_type: 'Pseudogley', texture: 'sandiger Lehm', nfk_mm: 109, gw_level: 0, sw_level: 3 }
    expect(soilLine(soil, 'en')).toBe('Soil (NRW soil map): Pseudogley, sandiger Lehm · holds a medium amount of water · tends to stay wet after rain')
    expect(soilLine({ soil_type: 'Gley', nfk_mm: 216, gw_level: 3, sw_level: 0 }, 'de')).toBe('Boden (Bodenkarte NRW): Gley · speichert viel Wasser · Grundwasser nah an der Oberfläche')
    expect(soilLine({}, 'en')).toBeNull()
    const lines = conditionLines({}, '', 'en', undefined, undefined, undefined, undefined, soil)
    expect(lines.some((l) => l.icon === '🟫')).toBe(true)
  })
})

it('adds the soil-moisture trend to the forecast line', () => {
  const fc = { fc_to: '2026-05-10', fc_rain_5d_mm: 1, fc_tmin_5d_c: 6, fc_frost_days: 0 }
  const text = (f: typeof fc & { fc_sm_change_5d?: number }, lang: 'en' | 'de' = 'en') =>
    conditionLines({}, '', lang, undefined, f).find((l) => l.icon === '☔')?.text
  expect(text({ ...fc, fc_sm_change_5d: -0.03 })).toContain('soil drying out')
  expect(text({ ...fc, fc_sm_change_5d: 0.03 }, 'de')).toContain('Boden wird feuchter')
  expect(text({ ...fc, fc_sm_change_5d: 0.01 })).not.toContain('soil')
  expect(text(fc)).not.toContain('soil')
})
