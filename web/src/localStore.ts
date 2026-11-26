export type LocalStore = Pick<Storage, 'getItem' | 'setItem'>
export const SNAPSHOT_KEY = 'cropews.local-data.v1'
export const WORK_KEYS = ['cropews.saved-fields.v1', 'cropews.checks.v1', 'cropews.observations.v1'] as const
export const unavailableStore: LocalStore = {
  getItem() { throw Error('Storage unavailable') }, setItem() { throw Error('Storage unavailable') },
}
/** After a restore, all work lives in one snapshot. Each change is one atomic storage write.
 * Legacy keys remain untouched; the snapshot takes precedence for the three work keys. */
export function localDataStore(raw: LocalStore): LocalStore {
  const snapshot = (): Record<string, string> | null => {
    const text = raw.getItem(SNAPSHOT_KEY)
    if (text == null) return null
    const data: unknown = JSON.parse(text)
    if (!data || typeof data !== 'object' || Array.isArray(data) || WORK_KEYS.some((k) => typeof (data as Record<string, unknown>)[k] !== 'string')) throw Error('Unreadable local snapshot')
    return data as Record<string, string>
  }
  return {
    getItem(key) { return (WORK_KEYS as readonly string[]).includes(key) ? snapshot()?.[key] ?? raw.getItem(key) : raw.getItem(key) },
    setItem(key, value) {
      const data = (WORK_KEYS as readonly string[]).includes(key) ? snapshot() : null
      if (data) raw.setItem(SNAPSHOT_KEY, JSON.stringify({ ...data, [key]: value }))
      else raw.setItem(key, value)
    },
  }
}
export function browserStore(): LocalStore | null {
  try { return localDataStore(window.localStorage) } catch { return null }
}
