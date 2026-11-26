import { SAVED_FIELDS_KEY, type LocalStore } from './savedFields'
import { STORAGE_KEY } from './fieldChecks'
import { OBS_STORAGE_KEY } from './observations'

export interface Backup {
  schema_version: 1
  exported_at: string
  saved_fields: unknown[]
  checks: Record<string, unknown>
  observations: unknown[]
  excluded: string[]
}
export function createBackup(store: LocalStore | null, now = new Date()): Backup {
  if (!store) throw Error('Storage unavailable')
  const saved_fields: unknown = JSON.parse(store.getItem(SAVED_FIELDS_KEY) ?? '[]')
  const checks: unknown = JSON.parse(store.getItem(STORAGE_KEY) ?? '{}')
  const observations: unknown = JSON.parse(store.getItem(OBS_STORAGE_KEY) ?? '[]')
  if (!Array.isArray(saved_fields) || !Array.isArray(observations) || !checks || typeof checks !== 'object' || Array.isArray(checks)) throw Error('Unreadable local records')
  return { schema_version: 1, exported_at: now.toISOString(), saved_fields, checks: checks as Record<string, unknown>, observations,
    excluded: ['Photo files, satellite images, offline caches and downloaded reports are not included. Photo references may be present.'] }
}
export function downloadBackup(backup: Backup) {
  const url = URL.createObjectURL(new Blob([JSON.stringify(backup, null, 2)], { type: 'application/json' }))
  const a = document.createElement('a')
  a.href = url; a.download = `crop-ews-backup-${backup.exported_at.slice(0, 10)}.json`
  a.click(); window.setTimeout(() => URL.revokeObjectURL(url), 1000)
}
export const BACKUP_STRINGS = {
  en: { choose: 'Choose a backup file', restore: 'Restore this backup', merge: 'Add to existing work', replace: 'Replace existing work', confirm: 'I understand this replaces my saved fields, checks and visit records.', rule: 'Adding keeps existing field names and skips identical checks and visits. Replacing removes current work. Missing monitored fields stay in My fields as unavailable.', invalid: 'This file is unreadable, unsupported or too large (maximum 5 MB). Nothing was changed.', restored: 'Restored on this device.', restoreError: 'Restore failed. Your existing work was kept.', preview: (f: number, c: number, v: number) => `${f} fields, ${c} checks and ${v} visits`, title: 'Backup and restore', download: 'Download my backup',
    contents: 'Includes saved field names, checks, notes and visit records. Photo files, satellite images, offline caches and reports are not included.',
    privacy: 'The backup may contain private field information. Keep it somewhere safe. Nothing is uploaded.',
    started: 'Backup download started. Keep the downloaded file to restore your work later.',
    error: 'Could not create a backup. Your browser storage may be unavailable or contain unreadable records.',
  },
  de: { choose: 'Sicherungsdatei auswählen', restore: 'Diese Sicherung wiederherstellen', merge: 'Zu vorhandenen Einträgen hinzufügen', replace: 'Vorhandene Einträge ersetzen', confirm: 'Ich verstehe, dass meine gespeicherten Felder, Prüfungen und Besuchseinträge ersetzt werden.', rule: 'Hinzufügen behält vorhandene Feldnamen und überspringt identische Prüfungen und Besuche. Ersetzen entfernt die bisherige Arbeit. Nicht mehr beobachtete Felder bleiben als nicht verfügbar sichtbar.', invalid: 'Diese Datei ist unlesbar, nicht unterstützt oder zu groß (höchstens 5 MB). Nichts wurde geändert.', restored: 'Auf diesem Gerät wiederhergestellt.', restoreError: 'Wiederherstellung fehlgeschlagen. Ihre bisherige Arbeit bleibt erhalten.', preview: (f: number, c: number, v: number) => `${f} Felder, ${c} Prüfungen und ${v} Besuche`, title: 'Sichern und wiederherstellen', download: 'Meine Sicherung herunterladen',
    contents: 'Enthält gespeicherte Feldnamen, Prüfungen, Notizen und Besuchseinträge. Fotodateien, Satellitenbilder, Offline-Daten und Berichte sind nicht enthalten.',
    privacy: 'Die Sicherung kann private Feldinformationen enthalten. Bewahren Sie sie sicher auf. Nichts wird hochgeladen.',
    started: 'Download gestartet. Bewahren Sie die Datei auf, um Ihre Arbeit später wiederherzustellen.',
    error: 'Sicherung fehlgeschlagen. Der Browserspeicher ist nicht verfügbar oder enthält unlesbare Einträge.',
  },
}
