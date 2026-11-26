import { expect, it } from 'vitest'
import type { SubfieldEntry } from './api'
import { patchSummary } from './patches'
const base: SubfieldEntry = { date: '2026-11-24', zones: [], quality: { clear: 1, cloud_shadow: 0, unstable: false, interior_px: 20 }, grid: { h: 1, w: 1, ndvi: [[0.5]], zone_cells: [] } }
it('never treats missing or insufficient evidence as no patches', () => {
  expect(patchSummary(base, 'en')).toContain('Not enough clear detail')
  expect(patchSummary({ ...base, assessment: { status: 'insufficient', usable_pixels: 1, clear_fraction: 0.1 } }, 'de')).toContain('Nicht genug')
})
it('distinguishes no detections from confirmed health', () => {
  const line = patchSummary({ ...base, assessment: { status: 'none_detected', usable_pixels: 20, clear_fraction: 1 } }, 'en')
  expect(line).toContain('No large uneven-growth areas')
  expect(line).toContain('does not confirm a healthy crop')
})
