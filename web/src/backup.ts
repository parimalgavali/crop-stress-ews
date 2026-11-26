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
  en: { title: 'Backup and restore', download: 'Download my backup',
    contents: 'Includes saved field names, checks, notes and visit records. Photo files, satellite images, offline caches and reports are not included.',
    privacy: 'The backup may contain private field information. Keep it somewhere safe. Nothing is uploaded.',
    started: 'Backup download started. Keep the downloaded file to restore your work later.',
    error: 'Could not create a backup. Your browser storage may be unavailable or contain unreadable records.',
  },
  de: { title: 'Sichern und wiederherstellen', download: 'Meine Sicherung herunterladen',
    contents: 'Enthält gespeicherte Feldnamen, Prüfungen, Notizen und Besuchseinträge. Fotodateien, Satellitenbilder, Offline-Daten und Berichte sind nicht enthalten.',
    privacy: 'Die Sicherung kann private Feldinformationen enthalten. Bewahren Sie sie sicher auf. Nichts wird hochgeladen.',
    started: 'Download gestartet. Bewahren Sie die Datei auf, um Ihre Arbeit später wiederherzustellen.',
    error: 'Sicherung fehlgeschlagen. Der Browserspeicher ist nicht verfügbar oder enthält unlesbare Einträge.',
  },
}
