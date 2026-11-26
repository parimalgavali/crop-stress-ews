import type { Backup } from './backup'
import { createBackup } from './backup'
import { localDataStore, SNAPSHOT_KEY, WORK_KEYS, type LocalStore } from './localStore'
import { SYMPTOMS, SEVERITIES, CAUSES, OBSERVER_TYPES } from './observations'

export const MAX_BACKUP_BYTES = 5 * 1024 * 1024
const obj = (v: unknown): v is Record<string, unknown> => !!v && typeof v === 'object' && !Array.isArray(v)
const str = (v: unknown, max = 10000): v is string => typeof v === 'string' && v.length <= max
const id = (v: unknown) => str(v, 200) && v.length > 0
const day = (v: unknown): v is string => str(v, 10) && /^\d{4}-\d{2}-\d{2}$/.test(v) && Number.isFinite(Date.parse(v)) && new Date(v).toISOString().slice(0, 10) === v
const timestamp = (v: unknown) => str(v, 50) && day(v.slice(0, 10)) && (v.length === 10 || /^\d{4}-\d{2}-\d{2}T/.test(v)) && Number.isFinite(Date.parse(v))
const optionalText = (v: unknown, max = 10000) => v === undefined || str(v, max)
const member = (v: unknown, values: readonly unknown[]) => values.includes(v)

/** Validate the entire document before any storage write. Unknown fields are rejected by schema version, not executed. */
export function parseBackup(text: string): Backup {
  if (new TextEncoder().encode(text).length > MAX_BACKUP_BYTES) throw Error('Backup too large')
  const b: unknown = JSON.parse(text)
  if (!obj(b) || b.schema_version !== 1 || !timestamp(b.exported_at) || !Array.isArray(b.saved_fields) || !obj(b.checks) || !Array.isArray(b.observations) || !Array.isArray(b.excluded) || !b.excluded.every((v) => str(v))) throw Error('Unsupported backup')
  const ids = new Set<string>()
  for (const f of b.saved_fields) {
    if (!obj(f) || !id(f.field_id) || !str(f.name, 80) || !str(f.district, 200) || ids.has(f.field_id as string)) throw Error('Invalid field')
    ids.add(f.field_id as string)
  }
  for (const [fid, checks] of Object.entries(b.checks)) {
    if (!id(fid) || !Array.isArray(checks) || checks.some((c) => !obj(c) || !day(c.date) || typeof c.ok !== 'boolean' || !member(c.light, [null, 'green', 'amber', 'red']) || !optionalText(c.note, 280))) throw Error('Invalid check')
  }
  for (const o of b.observations) {
    if (!obj(o) || o.schema_version !== 1 || !id(o.field_id) || !timestamp(o.observed_at) || !member(o.observer_type, OBSERVER_TYPES) || !member(o.symptom, SYMPTOMS) || !member(o.severity, [null, ...SEVERITIES]) || !member(o.suspected_cause, CAUSES) || !member(o.review_status, ['unreviewed', 'reviewed']) || !optionalText(o.note) || !optionalText(o.photo_ref)) throw Error('Invalid visit record')
  }
  return b as unknown as Backup
}
const canonical = (value: unknown): unknown => Array.isArray(value) ? value.map(canonical) : obj(value) ? Object.fromEntries(Object.keys(value).sort().map((key) => [key, canonical(value[key])])) : value
const unique = (items: unknown[]) => [...new Map(items.map((v) => [JSON.stringify(canonical(v)), v])).values()]
export function restoreBackup(raw: LocalStore | null, incoming: Backup, mode: 'merge' | 'replace'): Backup {
  if (!raw) throw Error('Storage unavailable')
  const store = localDataStore(raw)
  const current = parseBackup(JSON.stringify(createBackup(store)))
  const next = parseBackup(JSON.stringify(incoming))
  if (mode === 'merge') {
    next.saved_fields = [...next.saved_fields.filter((f) => !current.saved_fields.some((c) => (c as Record<string, unknown>).field_id === (f as Record<string, unknown>).field_id)), ...current.saved_fields]
    next.checks = Object.fromEntries([...new Set([...Object.keys(current.checks), ...Object.keys(next.checks)])].map((fid) => [fid, unique([...(Object.prototype.hasOwnProperty.call(current.checks, fid) ? current.checks[fid] as unknown[] : []), ...(Object.prototype.hasOwnProperty.call(next.checks, fid) ? next.checks[fid] as unknown[] : [])]).sort((a, b) => String((a as Record<string, unknown>).date).localeCompare(String((b as Record<string, unknown>).date)))]))
    next.observations = unique([...current.observations, ...next.observations])
  }
  const payload = [next.saved_fields, next.checks, next.observations]
  // All data changes together or not at all. Old keys are retained for recovery.
  store.setItem(SNAPSHOT_KEY, JSON.stringify(Object.fromEntries(WORK_KEYS.map((key, i) => [key, JSON.stringify(payload[i])]))))
  return next
}
export function backupCounts(b: Backup) {
  return { fields: b.saved_fields.length, checks: Object.values(b.checks).reduce<number>((n, a) => n + (a as unknown[]).length, 0), visits: b.observations.length }
}
