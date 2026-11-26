/** Personal names refer only to stable Live field ids (ADR 0034). */
export interface SavedField { field_id: string; name: string; district: string }
export const SAVED_FIELDS_KEY = 'cropews.saved-fields.v1'
import type { LocalStore } from './localStore'
export { browserStore, type LocalStore } from './localStore'
export function loadSavedFields(store: LocalStore | null): SavedField[] {
  try {
    const value: unknown = JSON.parse(store?.getItem(SAVED_FIELDS_KEY) ?? '[]')
    if (!Array.isArray(value)) return []
    return value.filter((x): x is SavedField => x != null && typeof x === 'object' &&
      typeof x.field_id === 'string' && x.field_id.length > 0 && typeof x.name === 'string' &&
      x.name.length <= 80 && typeof x.district === 'string')
      .filter((x, i, all) => all.findIndex((y) => y.field_id === x.field_id) === i)
  } catch { return [] }
}
export function saveFields(store: LocalStore | null, fields: SavedField[]): boolean {
  try {
    if (!store) return false
    store.setItem(SAVED_FIELDS_KEY, JSON.stringify(fields))
    return true
  } catch { return false }
}
export const SAVED_STRINGS = {
  en: { title: 'My fields', name: 'Name for this field', save: 'Save field name', remove: 'Remove',
    empty: 'No saved fields yet. Choose a Live field to save it.',
    privacy: 'Names are saved only in this browser on this device. No account is needed. Nothing is uploaded.',
    error: 'Could not save. Your browser storage may be full or unavailable.', saved: 'Saved on this device.',
    removed: 'Removed from My fields. Visit records are kept.', noForecast: 'No forecast available',
    unavailable: 'Not currently monitored', loading: 'Waiting for current data',
  },
  de: { title: 'Meine Felder', name: 'Name für dieses Feld', save: 'Feldname speichern', remove: 'Entfernen',
    empty: 'Noch keine Felder gespeichert. Wählen Sie ein Live-Feld zum Speichern.',
    privacy: 'Namen bleiben nur in diesem Browser auf diesem Gerät. Kein Konto nötig. Nichts wird hochgeladen.',
    error: 'Speichern fehlgeschlagen. Der Browserspeicher ist möglicherweise voll oder nicht verfügbar.',
    saved: 'Auf diesem Gerät gespeichert.', removed: 'Aus Meine Felder entfernt. Besuchseinträge bleiben erhalten.',
    noForecast: 'Keine Vorhersage verfügbar', unavailable: 'Wird derzeit nicht beobachtet', loading: 'Warte auf aktuelle Daten',
  },
}
