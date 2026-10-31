import { describe, expect, it } from 'vitest'
import { addCheck, agreement, lastCheckText, loadChecks, setNote, STORAGE_KEY, undoCheck } from './fieldChecks'

function memory() {
  const m = new Map<string, string>()
  return { getItem: (k: string) => m.get(k) ?? null, setItem: (k: string, v: string) => void m.set(k, v) }
}

describe('fieldChecks', () => {
  it('saves, undoes and survives bad stored data', () => {
    const s = memory()
    addCheck(s, 'A', { date: '2026-05-01', ok: false, light: 'red' })
    addCheck(s, 'A', { date: '2026-05-08', ok: true, light: 'green' })
    expect(loadChecks(s).A).toHaveLength(2)
    undoCheck(s, 'A')
    undoCheck(s, 'A')
    expect(loadChecks(s)).toEqual({})
    s.setItem(STORAGE_KEY, 'not json')
    expect(loadChecks(s)).toEqual({})
  })

  it('counts agreement only for checks made while a light was shown', () => {
    expect(
      agreement({
        A: [{ date: 'd', ok: false, light: 'amber' }, { date: 'd', ok: false, light: 'green' }],
        B: [{ date: 'd', ok: true, light: 'green' }, { date: 'd', ok: true, light: null }],
      }),
    ).toEqual({ n: 3, agree: 2 })
  })
})

  it('keeps a note on the latest check and speaks it', () => {
    const s = memory()
    addCheck(s, 'A', { date: '2026-05-01', ok: false, light: 'amber' })
    setNote(s, 'A', '  wet at the corner  ')
    expect(loadChecks(s).A[0].note).toBe('wet at the corner')
    expect(lastCheckText('A', 'en', s)).toContain('wet at the corner')
    setNote(s, 'A', '')
    expect(loadChecks(s).A[0].note).toBeUndefined()
    setNote(s, 'no-such-field', 'x')
    expect(loadChecks(s)['no-such-field']).toBeUndefined()
  })
