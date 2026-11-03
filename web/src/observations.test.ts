import { describe, expect, it } from 'vitest'
import { addObservation, exportEnvelope, loadObservations, OBS_SCHEMA_VERSION, type Observation } from './observations'

const mem = () => {
  const m = new Map<string, string>()
  return { getItem: (k: string) => m.get(k) ?? null, setItem: (k: string, v: string) => void m.set(k, v) }
}
const rec: Observation = {
  schema_version: 1, field_id: 'f1', observed_at: '2027-04-10',
  observer_type: 'farmer', symptom: 'yellowing', severity: 'mild',
  suspected_cause: 'unknown', review_status: 'unreviewed',
}

describe('observations', () => {
  it('round-trips records and tolerates corrupt storage', () => {
    const s = mem()
    expect(loadObservations(s)).toEqual([])
    expect(addObservation(s, rec)).toEqual([rec])
    expect(loadObservations(s)).toEqual([rec])
    const bad = mem(); bad.setItem('cropews.observations.v1', '{nope')
    expect(loadObservations(bad)).toEqual([])
  })
  it('exports a versioned envelope', () => {
    const env = exportEnvelope([rec])
    expect(env.schema_version).toBe(OBS_SCHEMA_VERSION)
    expect(env.records).toEqual([rec])
    expect(env.exported_at).toBeTruthy()
  })
})
