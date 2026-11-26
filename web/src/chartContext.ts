import type { PeerSupport, SeriesPoint } from './api'
import type { Lang } from './i18n'
export interface ChartContext { district?: string; peerKind?: 'cereal' | 'all'; peerSupport?: PeerSupport }
export const COMPARISON_TEXT = {
  en: { mixed: 'Mixed monitored crops', cereal: 'Likely winter cereals (satellite estimate)', unknown: 'Comparison crop group unknown',
    districtUnknown: 'District not reported', countUnknown: 'Number of contributing fields unknown',
    count: (n: number) => `${n} contributing fields`,
    caution: 'Crops, planting dates and growth stages can differ. A lower greenness value does not prove poor crop health.',
  },
  de: { mixed: 'Gemischte beobachtete Kulturen', cereal: 'Wahrscheinlich Wintergetreide (Satellitenschätzung)', unknown: 'Kulturgruppe des Vergleichs unbekannt',
    districtUnknown: 'Kreis nicht angegeben', countUnknown: 'Anzahl beitragender Felder unbekannt',
    count: (n: number) => `${n} beitragende Felder`,
    caution: 'Kulturen, Aussaattermine und Wachstumsstadien können abweichen. Ein niedrigerer Grünwert beweist keinen schlechten Bestandszustand.',
  },
}
export function comparisonGroup(context: ChartContext, lang: Lang): string {
  const t = COMPARISON_TEXT[lang]
  return context.peerKind === 'all' ? t.mixed : context.peerKind === 'cereal' ? t.cereal : t.unknown
}
export function comparisonContext(series: SeriesPoint[], peers: SeriesPoint[] | undefined, context: ChartContext, lang: Lang): string {
  const t = COMPARISON_TEXT[lang]
  const last = series.at(-1)?.[0]
  const date = peers?.filter(([d]) => last && d <= last).at(-1)?.[0]
  const n = date ? context.peerSupport?.[date]?.count : undefined
  return `${comparisonGroup(context, lang)} · ${context.district || t.districtUnknown} · ${date ?? '—'} · ${n == null ? t.countUnknown : t.count(n)}. ${t.caution}`
}
