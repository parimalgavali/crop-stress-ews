import type { PeerSupport, SeriesPoint } from './api'
import type { Lang } from './i18n'
export interface ChartContext { district?: string; peerKind?: 'cereal' | 'all'; peerSupport?: PeerSupport }
export const COMPARISON_TEXT = {
  en: { mixed: 'Mixed monitored crops', cereal: 'Likely winter cereals (satellite estimate)', unknown: 'Comparison crop group unknown',
    districtUnknown: 'District not reported', countUnknown: 'Number of contributing fields unknown',
    count: (n: number) => `${n} contributing fields`,
    missing: 'Comparison unavailable: no same-date group observation.', unknownSupport: 'Comparison unavailable: contributing-field count is unknown.', few: 'Comparison unavailable: fewer than five contributing fields.', unknownGroup: 'Comparison unavailable: crop group is unknown.',
    changed: 'Contributing fields changed since the previous group observation. Line changes may partly reflect different fields.', historyUnknown: 'Earlier comparison coverage is unknown.',
    caution: 'Crops, planting dates and growth stages can differ. A lower greenness value does not prove poor crop health.',
  },
  de: { mixed: 'Gemischte beobachtete Kulturen', cereal: 'Wahrscheinlich Wintergetreide (Satellitenschätzung)', unknown: 'Kulturgruppe des Vergleichs unbekannt',
    districtUnknown: 'Kreis nicht angegeben', countUnknown: 'Anzahl beitragender Felder unbekannt',
    count: (n: number) => `${n} beitragende Felder`,
    missing: 'Vergleich nicht verfügbar: keine Gruppenbeobachtung vom selben Tag.', unknownSupport: 'Vergleich nicht verfügbar: Anzahl beitragender Felder unbekannt.', few: 'Vergleich nicht verfügbar: weniger als fünf beitragende Felder.', unknownGroup: 'Vergleich nicht verfügbar: Kulturgruppe unbekannt.',
    changed: 'Seit der vorherigen Gruppenbeobachtung tragen andere Felder bei. Linienänderungen können teilweise auf anderen Feldern beruhen.', historyUnknown: 'Frühere Vergleichsabdeckung unbekannt.',
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
  const date = peers?.find(([d]) => last && d === last)?.[0]
  const n = date ? context.peerSupport?.[date]?.count : undefined
  const quality = !date ? t.missing : n == null ? t.unknownSupport : n < 5 ? t.few : !context.peerKind ? t.unknownGroup : ''
  const coverage = date ? coverageText(context.peerSupport?.[date], lang) : ''
  return `${comparisonGroup(context, lang)} · ${context.district || t.districtUnknown} · ${date ?? '—'} · ${n == null ? t.countUnknown : t.count(n)}. ${quality} ${coverage} ${t.caution}`
}

export function coverageText(support: import('./api').PeerDateSupport | undefined, lang: Lang): string {
  const t = COMPARISON_TEXT[lang]
  if (!support || support.previous_count == null || support.retained_from_previous == null) return t.historyUnknown
  return support.retained_from_previous < support.count || support.retained_from_previous < support.previous_count ? t.changed : ''
}
