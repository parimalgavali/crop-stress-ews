import { describe, expect, it, vi } from 'vitest';
import { createVisitCsv, visitsCsv } from './visitCsv';
import { OBS_STORAGE_KEY, type Observation } from './observations';
const visit: Observation = { schema_version: 1, field_id: 'LWK-1', observed_at: '2026-11-27', observer_type: 'farmer', symptom: 'standing_water', severity: null, suspected_cause: 'unknown', review_status: 'unreviewed', note: 'Müller: "Wasser", near gate\nSecond line' };
describe('visit CSV', () => {
  it('exports readable names and preserves UTF-8, commas, quotes, newlines and uncertainty', () => {
    const text = visitsCsv([visit], [{ field_id: 'LWK-1', name: 'Über dem Bach', district: 'Soest' }], 'en');
    expect(text.startsWith('\ufeff"Field ID","Local field name","Visit date"')).toBe(true);
    expect(text).toContain('"LWK-1","Über dem Bach","2026-11-27","farmer","standing water","not sure","not sure","Not reviewed"');
    expect(text).toContain('"Müller: ""Wasser"", near gate\nSecond line"\r\n');
    const german = visitsCsv([{ ...visit, severity: 'moderate', review_status: 'reviewed' }], [], 'de');
    expect(german).toContain('"Nicht benannt"');
    expect(german).toContain('"stehendes Wasser","mittel","unsicher","Geprüft"');
  });
  it.each(['=1+1', '+SUM(A1)', '-1+2', '@SUM(A1)', '  =1+1', '\t=1+1', '\r=1+1', '\n=1+1', '\u200b=1+1', '\ufeff=1+1'])('neutralises formula text %j in IDs, field names and notes', (value) => {
    const csv = visitsCsv([{ ...visit, field_id: value, note: value }], [{ field_id: value, name: value, district: 'Soest' }], 'en');
    const quoted = `"'${value}"`;
    expect(csv).toContain(`${quoted},${quoted},"2026-11-27"`);
    expect(csv.endsWith(`${quoted}\r\n`)).toBe(true);
  });
  it('reads fresh stored work without writes and rejects unreadable or unsupported data', () => {
    let raw = JSON.stringify([visit]);
    const store = { getItem: (key: string) => key === OBS_STORAGE_KEY ? raw : '[]', setItem: vi.fn() };
    expect(createVisitCsv(store, 'en')).toContain('standing water');
    expect(store.setItem).not.toHaveBeenCalled();
    raw = 'not JSON'; expect(() => createVisitCsv(store, 'en')).toThrow();
    raw = JSON.stringify([{ ...visit, symptom: 'unrecognised' }]); expect(() => createVisitCsv(store, 'en')).toThrow();
    expect(store.setItem).not.toHaveBeenCalled();
  });
});
