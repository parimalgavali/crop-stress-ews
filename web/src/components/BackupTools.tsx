import { useState } from 'react'
import type { Lang } from '../i18n'
import { browserStore, type LocalStore } from '../savedFields'
import { BACKUP_STRINGS, createBackup, downloadBackup } from '../backup'
export function BackupTools({ lang, store = browserStore(), download = downloadBackup }: {
  lang: Lang; store?: LocalStore | null; download?: typeof downloadBackup
}) {
  const t = BACKUP_STRINGS[lang]
  const [status, setStatus] = useState<'started' | 'error' | null>(null)
  return <section className="backup-tools" aria-label={t.title}>
    <h2>{t.title}</h2><p>{t.contents}</p><p className="hint">{t.privacy}</p>
    <button type="button" onClick={() => {
      try { download(createBackup(store)); setStatus('started') } catch { setStatus('error') }
    }}>{t.download}</button>
    {status && <p role={status === 'error' ? 'alert' : 'status'}>{t[status]}</p>}
  </section>
}
