import { useState } from 'react'
import type { LiveSeason } from '../api'
import { STRINGS, type Lang } from '../i18n'
import { worstLevel } from '../live'
import { browserStore, loadSavedFields, saveFields, SAVED_STRINGS, type LocalStore, type SavedField } from '../savedFields'

export function MyFields({ live, selected, onSelect, lang, store = browserStore() }: {
  live: LiveSeason | null; selected: string | null; onSelect: (id: string) => void; lang: Lang; store?: LocalStore | null
}) {
  const t = SAVED_STRINGS[lang]
  const [fields, setFields] = useState(() => loadSavedFields(store))
  const [status, setStatus] = useState<'saved' | 'removed' | 'error' | null>(null)
  const current = live?.fields.features.find((f) => f.properties.field_id === selected)
  const update = (next: SavedField[], message: 'saved' | 'removed') => {
    if (!saveFields(store, next)) return setStatus('error')
    setFields(next); setStatus(message)
  }
  return <section className="my-fields" aria-label={t.title}>
    <h2>{t.title}</h2>
    <p className="hint">{t.privacy}</p>
    {!fields.length && <p>{t.empty}</p>}
    <ul>{fields.map((f) => {
      const available = live?.fields.features.some((x) => x.properties.field_id === f.field_id)
      const level = available ? worstLevel(live?.risk?.[f.field_id]) : null
      const label = !live ? t.loading : !available ? t.unavailable : level ? STRINGS[lang].level[level] : t.noForecast
      return <li key={f.field_id}>
        <button type="button" disabled={!available} onClick={() => onSelect(f.field_id)}>{f.name || f.field_id}</button>
        <span> · {f.district} · {label}</span>{' '}
        <button type="button" aria-label={`${t.remove}: ${f.name || f.field_id}`} onClick={() => update(fields.filter((x) => x.field_id !== f.field_id), 'removed')}>{t.remove}</button>
      </li>
    })}</ul>
    {current && <form key={current.properties.field_id} onSubmit={(event) => {
      event.preventDefault()
      const name = String(new FormData(event.currentTarget).get('name') ?? '').trim().slice(0, 80)
      const field = { field_id: current.properties.field_id, name, district: current.properties.district }
      update([...fields.filter((f) => f.field_id !== field.field_id), field], 'saved')
    }}>
      <label htmlFor="saved-field-name">{t.name}</label>
      <input id="saved-field-name" name="name" maxLength={80} defaultValue={fields.find((f) => f.field_id === selected)?.name ?? ''} />
      <button type="submit">{t.save}</button>
    </form>}
    {status && <p role={status === 'error' ? 'alert' : 'status'}>{t[status]}</p>}
  </section>
}
