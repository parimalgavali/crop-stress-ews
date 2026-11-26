import { afterEach, expect, it } from 'vitest'
import { createBackup } from './backup'
import { SAVED_FIELDS_KEY } from './savedFields'
import { STORAGE_KEY } from './fieldChecks'
import { OBS_STORAGE_KEY } from './observations'
afterEach(() => localStorage.clear())
it('backs up all local work including notes and preserves original ids', () => {
  const fields = [{ field_id: 'a', name: 'North', district: 'Soest' }]
  const checks = { a: [{ date: '2027-04-05', ok: false, light: 'red', note: 'Wet' }] }
  const observations = [{ field_id: 'a', note: 'Visit note', photo_ref: 'local-photo' }]
  localStorage.setItem(SAVED_FIELDS_KEY, JSON.stringify(fields))
  localStorage.setItem(STORAGE_KEY, JSON.stringify(checks))
  localStorage.setItem(OBS_STORAGE_KEY, JSON.stringify(observations))
  const backup = createBackup(localStorage, new Date('2027-04-06T00:00:00Z'))
  expect(backup).toMatchObject({ schema_version: 1, saved_fields: fields, checks, observations })
  expect(backup.excluded.join(' ')).toContain('Photo files')
  expect(backup.exported_at).toBe('2027-04-06T00:00:00.000Z')
})
it('never silently exports an empty backup when storage cannot be read', () => {
  expect(() => createBackup(null)).toThrow()
  expect(() => createBackup({ getItem: () => { throw Error('blocked') }, setItem() {} })).toThrow()
  localStorage.setItem(STORAGE_KEY, '{broken')
  expect(() => createBackup(localStorage)).toThrow()
})
