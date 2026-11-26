import { useRef, useState } from 'react'
import type { Lang } from '../i18n'
import { browserStore, type LocalStore } from '../savedFields'
import { backupCounts, MAX_BACKUP_BYTES, parseBackup, restoreBackup } from '../restore'
import type { Backup } from '../backup'
import { BACKUP_STRINGS, createBackup, downloadBackup } from '../backup'
export function BackupTools({ lang, store = browserStore(), download = downloadBackup, onRestored }: {
  lang: Lang; store?: LocalStore | null; download?: typeof downloadBackup; onRestored?: () => void
}) {
  const t = BACKUP_STRINGS[lang]
  const [status, setStatus] = useState<'started' | 'error' | 'invalid' | 'restored' | 'restoreError' | null>(null)
  const [preview, setPreview] = useState<Backup | null>(null)
  const [mode, setMode] = useState<'merge' | 'replace'>('merge')
  const [confirmed, setConfirmed] = useState(false)
  const fileRead = useRef(0)
  const [result, setResult] = useState('')
  return <section className="backup-tools" aria-label={t.title}>
    <h2>{t.title}</h2><p>{t.contents}</p><p className="hint">{t.privacy}</p>
    <button type="button" onClick={() => {
      try { download(createBackup(store)); setStatus('started') } catch { setStatus('error') }
    }}>{t.download}</button>
    <label className="backup-file">{t.choose}<input type="file" accept=".json,application/json" onChange={async (e) => {
      const file = e.target.files?.[0]
      const request = ++fileRead.current
      setPreview(null); setConfirmed(false); setMode('merge'); setStatus(null)
      if (!file) return
      try {
        if (file.size > MAX_BACKUP_BYTES) throw Error('Too large')
        const parsed = parseBackup(await file.text())
        if (request === fileRead.current) setPreview(parsed)
      } catch { if (request === fileRead.current) setStatus('invalid') }
    }} /></label>
    {preview && <div>
      <p>{preview.exported_at} · {t.preview(backupCounts(preview).fields, backupCounts(preview).checks, backupCounts(preview).visits)}</p>
      <p>{t.rule}</p>
      <label><input type="radio" name="restore-mode" checked={mode === 'merge'} onChange={() => { setMode('merge'); setConfirmed(false) }} />{t.merge}</label>
      <label><input type="radio" name="restore-mode" checked={mode === 'replace'} onChange={() => setMode('replace')} />{t.replace}</label>
      {mode === 'replace' && <label><input type="checkbox" checked={confirmed} onChange={(e) => setConfirmed(e.target.checked)} />{t.confirm}</label>}
      <button type="button" disabled={mode === 'replace' && !confirmed} onClick={() => {
        try {
          const restored = restoreBackup(store, preview, mode)
          const counts = backupCounts(restored)
          setPreview(null); setStatus('restored'); setResult(t.preview(counts.fields, counts.checks, counts.visits)); onRestored?.()
        } catch { setStatus('restoreError') }
      }}>{t.restore}</button>
    </div>}
    {status && <p role={['error', 'invalid', 'restoreError'].includes(status) ? 'alert' : 'status'}>{t[status]} {status === 'restored' ? result : ''}</p>}
  </section>
}
