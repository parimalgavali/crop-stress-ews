import { cleanup, render, screen } from '@testing-library/react'
import { afterEach, expect, it } from 'vitest'
import { SubfieldMap } from './SubfieldMap'
import type { SubfieldEntry } from '../api'
afterEach(cleanup)
it('explains the grid, date and limits without calling an even field healthy', () => {
  const entry: SubfieldEntry = { date: '2026-11-24', assessment: { status: 'none_detected', usable_pixels: 20, clear_fraction: 1 }, zones: [], quality: { clear: 1, cloud_shadow: 0, unstable: false, interior_px: 20 }, grid: { h: 1, w: 2, ndvi: [[0.4, null]], zone_cells: [] } }
  render(<SubfieldMap entry={entry} lang="en" />)
  expect(screen.getByRole('img')).toHaveAccessibleName(/2026-11-24/)
  expect(screen.getByText(/not a normal photo/)).toBeInTheDocument()
  expect(screen.getByText(/Display squares may combine/)).toBeInTheDocument()
  expect(screen.getByText(/Outside the usable field/)).toBeInTheDocument()
  expect(screen.getByRole('img')).toHaveTextContent('+—')
})
