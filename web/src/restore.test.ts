import { afterEach, expect, it } from 'vitest'
import { createBackup } from './backup'
import { parseBackup, restoreBackup } from './restore'
import { localDataStore, SNAPSHOT_KEY } from './localStore'
import { SAVED_FIELDS_KEY } from './savedFields'
import { STORAGE_KEY } from './fieldChecks'
const a = { field_id: 'a', name: 'North', district: 'Soest' }
const check = { date: '2027-04-05', ok: false, light: 'red', note: 'Wet' }
afterEach(() => localStorage.clear())
function fixture() {
  const b = createBackup(localStorage)
  b.saved_fields = [a]; b.checks = { a: [check] }
  return b
}
it('validates before replacing anything and rejects unsupported or malformed files', () => {
  const b = fixture()
  expect(parseBackup(JSON.stringify(b)).saved_fields).toEqual([a])
  for (const invalid of [{ ...b, schema_version: 2 }, { ...b, saved_fields: [a, a] }, { ...b, checks: { a: [{ ...check, date: '2027-02-31' }] } }, { ...b, observations: [{ field_id: 'a' }] }]) {
    expect(() => restoreBackup(localStorage, invalid as typeof b, 'replace')).toThrow()
    expect(localStorage.getItem(SNAPSHOT_KEY)).toBeNull()
  }
})
it('merges without overwriting existing names or repeating identical records', () => {
  localStorage.setItem(SAVED_FIELDS_KEY, JSON.stringify([{ ...a, name: 'Existing' }]))
  localStorage.setItem(STORAGE_KEY, JSON.stringify({ a: [check] }))
  const b = fixture()
  restoreBackup(localStorage, b, 'merge')
  restoreBackup(localStorage, b, 'merge')
  const store = localDataStore(localStorage)
  expect(createBackup(store).saved_fields).toEqual([{ ...a, name: 'Existing' }])
  expect(createBackup(store).checks).toEqual({ a: [check] })
  store.setItem(STORAGE_KEY, JSON.stringify({ a: [{ ...check, note: 'Updated after restore' }] }))
  expect(createBackup(store).checks).toEqual({ a: [{ ...check, note: 'Updated after restore' }] })
})
it('replaces the entire work set in a single write', () => {
  localStorage.setItem(SAVED_FIELDS_KEY, JSON.stringify([{ ...a, field_id: 'old' }]))
  restoreBackup(localStorage, fixture(), 'replace')
  expect(createBackup(localDataStore(localStorage)).saved_fields).toEqual([a])
  // Retained legacy keys are not consulted after a snapshot exists.
  expect(JSON.parse(localStorage.getItem(SAVED_FIELDS_KEY)!)[0].field_id).toBe('old')
})
it('keeps all old data when the snapshot write fails', () => {
  localStorage.setItem(SAVED_FIELDS_KEY, JSON.stringify([a]))
  const b = fixture()
  const before = JSON.stringify(localStorage)
  expect(() => restoreBackup({ getItem: (k) => localStorage.getItem(k), setItem: () => { throw Error('quota') } }, b, 'replace')).toThrow()
  expect(JSON.stringify(localStorage)).toBe(before)
})
