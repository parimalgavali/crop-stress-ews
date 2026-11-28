import type { Lang } from './i18n';
import { OBS_STORAGE_KEY, type Observation } from './observations';
import { OBS_TEXT } from './observationText';
import { parseBackup } from './restore';
import { SAVED_FIELDS_KEY, type LocalStore, type SavedField } from './savedFields';

export const CSV_TEXT = {
  en: {
    export: 'Export all visits (CSV)',
    hint: 'CSV is for reading in a spreadsheet, not for restoring the app. Use Backup and restore for that. It includes private notes. Unreviewed visits are observations, not confirmed diagnoses.',
    saved: 'CSV download started. Your records have not changed.',
    error: 'CSV export failed. Stored visits or field names could not be read. Nothing was changed.',
    unnamed: 'Not named', reviewed: 'Reviewed', unreviewed: 'Not reviewed',
    headers: ['Field ID', 'Local field name', 'Visit date', 'Visitor', 'Finding', 'Severity', 'Suspected cause', 'Review status', 'Note'],
  },
  de: {
    export: 'Alle Besuche exportieren (CSV)',
    hint: 'CSV dient zum Lesen in einer Tabellenkalkulation, nicht zum Wiederherstellen der App. Nutzen Sie dafür Sichern und wiederherstellen. Enthält private Notizen. Ungeprüfte Besuche sind Beobachtungen, keine bestätigten Diagnosen.',
    saved: 'CSV-Download gestartet. Ihre Einträge wurden nicht verändert.',
    error: 'CSV-Export fehlgeschlagen. Besuchseinträge oder Feldnamen konnten nicht gelesen werden. Nichts wurde geändert.',
    unnamed: 'Nicht benannt', reviewed: 'Geprüft', unreviewed: 'Nicht geprüft',
    headers: ['Feld-ID', 'Eigener Feldname', 'Besuchsdatum', 'Besucher/in', 'Beobachtung', 'Schweregrad', 'Vermutete Ursache', 'Prüfstatus', 'Notiz'],
  },
};
/** Quotes preserve commas/newlines; the apostrophe prevents spreadsheet formula execution. */
function cell(value: string): string {
  const unsafe = /^[\s\p{Cc}\p{Cf}]*[=+\-@]/u.test(value) || /^[\t\r\n]/.test(value);
  return `"${(unsafe ? "'" + value : value).replace(/"/g, '""')}"`;
}
export function visitsCsv(records: Observation[], names: SavedField[], lang: Lang): string {
  const t = CSV_TEXT[lang], o = OBS_TEXT[lang];
  const rows = records.map((r) => [r.field_id, names.find((n) => n.field_id === r.field_id)?.name || t.unnamed,
    r.observed_at, o.labels[r.observer_type], o.labels[r.symptom], r.severity ? o.labels[r.severity] : o.unknown,
    r.suspected_cause === 'unknown' ? o.unknown : o.labels[r.suspected_cause], t[r.review_status], r.note ?? '']);
  // UTF-8 BOM helps Excel recognise names such as Müller; CRLF is the standard CSV row ending.
  return '\ufeff' + [t.headers, ...rows].map((row) => row.map(cell).join(',')).join('\r\n') + '\r\n';
}
export function createVisitCsv(store: LocalStore, lang: Lang): string {
  // Validate just the two sources this report needs. Never silently turn unreadable data into an empty export.
  const data = parseBackup(JSON.stringify({ schema_version: 1, exported_at: new Date().toISOString(),
    saved_fields: JSON.parse(store.getItem(SAVED_FIELDS_KEY) ?? '[]'), checks: {},
    observations: JSON.parse(store.getItem(OBS_STORAGE_KEY) ?? '[]'), excluded: [] }));
  return visitsCsv(data.observations as Observation[], data.saved_fields as SavedField[], lang);
}
export function downloadVisitCsv(store: LocalStore, lang: Lang) {
  const text = createVisitCsv(store, lang);
  const url = URL.createObjectURL(new Blob([text], { type: 'text/csv;charset=utf-8' }));
  const a = document.createElement('a'); a.href = url; a.download = `field-visits-${new Date().toISOString().slice(0, 10)}.csv`;
  a.click(); window.setTimeout(() => URL.revokeObjectURL(url), 1000);
}
