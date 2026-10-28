import { describe, expect, it } from 'vitest'
import { conditionLines, greenness, radarChanged, trend } from './live'

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
})
