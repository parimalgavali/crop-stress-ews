import { describe, expect, it } from 'vitest'
import { maskRgb, outerRing } from './fieldPhoto'

describe('field photo', () => {
  it('takes the exterior of the largest polygon', () => {
    const small = [[0, 0], [1, 0], [1, 1], [0, 0]]
    const big = [[5, 5], [9, 5], [9, 9], [5, 5]]
    expect(outerRing({ type: 'Polygon', coordinates: [small] })).toEqual(small)
    expect(outerRing({ type: 'MultiPolygon', coordinates: [[small], [big]] })).toEqual(big)
    expect(outerRing({ type: 'Point', coordinates: [0, 0] })).toBeNull()
  })

  it('keeps pixels inside the border and hides the rest and no-data', () => {
    // 2x2 grid with centres at (0.5,0.5) (1.5,0.5) (0.5,1.5) (1.5,1.5); ring covers the left column
    const ring: [number, number][] = [[0, 0], [1, 0], [1, 2], [0, 2], [0, 0]]
    const r = [10, 20, 0, 40]
    const out = maskRgb([r, r, r], 2, 2, (i, j) => [i + 0.5, j + 0.5], ring)
    expect(Array.from(out.filter((_, k) => k % 4 === 3))).toEqual([255, 0, 0, 0])
    expect(Array.from(out.slice(0, 3))).toEqual([10, 10, 10])
  })
})
