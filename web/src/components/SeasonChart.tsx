import { comparisonGroup, type ChartContext } from '../chartContext'
import type { SeriesPoint } from '../api'
import { formatDate, type Lang } from '../i18n'
import { chartSummary, LIVE_STRINGS } from '../live'
export interface ChartProps extends ChartContext {
  series?: SeriesPoint[]; peers?: SeriesPoint[]; peerKind?: 'cereal' | 'all'; lang: Lang
}
export const CHART_TEXT = {
  en: { axis: 'Greenness (NDVI)', values: 'Observation dates and values', date: 'Date',
    explain: 'Dots are usable satellite observations; lines only connect them. Gaps are not daily measurements. NDVI ranges from −1 to 1 and is a vegetation signal, not a percentage of crop health or a harvest prediction.',
  },
  de: { axis: 'Pflanzengrün (NDVI)', values: 'Beobachtungsdaten und Werte', date: 'Datum',
    explain: 'Punkte sind nutzbare Satellitenbeobachtungen; Linien verbinden sie nur. Lücken sind keine täglichen Messungen. NDVI reicht von −1 bis 1 und ist ein Vegetationssignal, kein Gesundheitsprozentsatz und keine Erntevorhersage.',
  },
}
const W = 400, H = 170, LEFT = 40, RIGHT = 12, TOP = 12, BOTTOM = 35
const day = (d: string) => Date.parse(`${d}T00:00:00Z`) / 86400000
export function SeasonChart({ series, peers, peerKind, peerSupport, district, lang }: ChartProps) {
  const summary = chartSummary(series, peers, lang, { peerKind, peerSupport, district })
  if (!series || !summary) return null
  const t = CHART_TEXT[lang], l = LIVE_STRINGS[lang]
  const all = [...series, ...(peers ?? [])]
  const first = all.reduce((a, b) => a[0] < b[0] ? a : b)[0]
  const last = all.reduce((a, b) => a[0] > b[0] ? a : b)[0]
  const t0 = day(first), t1 = Math.max(day(last), t0 + 1)
  const x = (d: string) => LEFT + (day(d) - t0) / (t1 - t0) * (W - LEFT - RIGHT)
  const y = (v: number) => TOP + (1 - v) / 2 * (H - TOP - BOTTOM)
  const path = (s: SeriesPoint[]) => s.map(([d, v], i) => `${i ? 'L' : 'M'}${x(d)},${y(v)}`).join(' ')
  const value = (v: number) => v.toLocaleString(lang, { minimumFractionDigits: 2, maximumFractionDigits: 2 })
  return <figure className="season-chart" data-testid="season-chart">
    <figcaption>{l.chartTitle}</figcaption><p>{t.axis}</p>
    <svg viewBox={`0 0 ${W} ${H}`} role="img" aria-label={`${summary}. ${t.explain}`}>
      {[-1, 0, 1].map((v) => <g key={v} aria-hidden="true">
        <line x1={LEFT} x2={W - RIGHT} y1={y(v)} y2={y(v)} stroke="#ddd" />
        <text x={LEFT - 8} y={y(v) + 4} textAnchor="end" fontSize="12">{v}</text>
      </g>)}
      {peers && peers.length > 1 && <path d={path(peers)} className="peers" fill="none" />}
      <path d={path(series)} className="field" fill="none" />
      {series.map(([d, v]) => <circle key={d} cx={x(d)} cy={y(v)} r={3.5} className="field"><title>{d}: {value(v)}</title></circle>)}
      <text x={LEFT} y={H - 8} fontSize="12">{formatDate(first, lang)}</text>
      <text x={W - RIGHT} y={H - 8} fontSize="12" textAnchor="end">{formatDate(last, lang)}</text>
    </svg>
    <p className="legend"><span className="key field">━●</span> {l.chartField}{peers && peers.length > 1 && <> <span className="key peers">╌╌</span> {comparisonGroup({ peerKind }, lang)}</>}</p>
    <p className="hint">{summary}</p><p className="hint">{t.explain}</p>
    <details><summary>{t.values}</summary><div className="observation-table">
      <table><thead><tr><th scope="col">{t.date}</th><th scope="col">{t.axis}</th></tr></thead>
        <tbody>{series.map(([d, v]) => <tr key={d}><th scope="row">{d}</th><td>{value(v)}</td></tr>)}</tbody>
      </table>
    </div></details>
  </figure>
}
