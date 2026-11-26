import type { SubfieldEntry } from '../api'
import type { Lang } from '../i18n'
import { PATCH_TEXT, patchSummary } from '../patches'

function cell(v: number | null, candidate: boolean) {
  if (v == null) return { color: '#eee', mark: '—' }
  if (candidate) return { color: '#b3261e', mark: '×' }
  if (v < 0.3) return { color: '#c9b98a', mark: '·' }
  if (v < 0.6) return { color: '#7fae57', mark: '+' }
  return { color: '#2e7d32', mark: '●' }
}
export function SubfieldMap({ entry, lang }: { entry: SubfieldEntry; lang: Lang }) {
  const t = PATCH_TEXT[lang]
  const zone = new Set(entry.grid.zone_cells.map(([r, c]) => `${r},${c}`))
  const text = patchSummary(entry, lang)
  return <section className="subfield" aria-label={t.title}>
    <h3>{t.title}</h3>
    <p>{t.explain}</p>
    <div role="img" aria-label={text} className="subfield-grid" style={{
      display: 'grid', gridTemplateColumns: `repeat(${entry.grid.w}, minmax(0, 1fr))`, width: `${entry.grid.w * 10}px`, maxWidth: '100%', gap: 1,
    }}>
      {entry.grid.ndvi.flatMap((row, r) => row.map((v, c) => {
        const x = cell(v, zone.has(`${r},${c}`) && entry.assessment?.status === 'detected')
        return <span key={`${r}-${c}`} aria-hidden="true" style={{ aspectRatio: '1', background: x.color, fontSize: 8, lineHeight: 1, textAlign: 'center', color: x.mark === '×' || x.mark === '●' ? '#fff' : '#111' }}>{x.mark}</span>
      }))}
    </div>
    <ul className="patch-legend">{t.legend.map((line) => <li key={line}>{line}</li>)}</ul>
    <p className="hint">{text}</p><p className="hint">{t.detail}</p>
  </section>
}
