import type { FieldRisk, Level, Reason } from './api'

export type Lang = 'en' | 'de'

export const STRINGS = {
  en: {
    title: 'Crop stress warning',
    subtitle: 'Winter wheat, North Rhine-Westphalia',
    field: 'Field',
    chooseField: 'Choose a field',
    pickHint: 'Tap a field on the map or choose one from the list.',
    day: 'Day',
    play: 'Play season',
    pause: 'Pause',
    listen: 'Listen',
    stop: 'Stop',
    why: 'Why',
    nothing: 'Nothing unusual',
    noData: 'No forecast for this day',
    inDays: (d: number) => `Next ${d} days`,
    level: { green: 'Low risk', amber: 'Watch', red: 'High risk' } as Record<Level, string>,
    season: 'Season',
    language: 'Language',
  },
  de: {
    title: 'Warnung vor Pflanzenstress',
    subtitle: 'Winterweizen, Nordrhein-Westfalen',
    field: 'Feld',
    chooseField: 'Feld auswählen',
    pickHint: 'Tippen Sie auf ein Feld in der Karte oder wählen Sie es aus der Liste.',
    day: 'Tag',
    play: 'Saison abspielen',
    pause: 'Pause',
    listen: 'Vorlesen',
    stop: 'Stopp',
    why: 'Warum',
    nothing: 'Nichts Auffälliges',
    noData: 'Keine Vorhersage für diesen Tag',
    inDays: (d: number) => `Nächste ${d} Tage`,
    level: { green: 'Geringes Risiko', amber: 'Beobachten', red: 'Hohes Risiko' } as Record<
      Level,
      string
    >,
    season: 'Saison',
    language: 'Sprache',
  },
}

export const reasonText = (r: Reason, lang: Lang) => (lang === 'de' ? r.text_de : r.text_en)

export function formatDate(iso: string, lang: Lang): string {
  return new Date(`${iso}T00:00:00`).toLocaleDateString(lang === 'de' ? 'de-DE' : 'en-GB', {
    day: 'numeric',
    month: 'long',
  })
}

/** One short spoken summary: each horizon's level, then the reasons of the worst horizon. */
export function speechText(risk: FieldRisk, lang: Lang): string {
  const s = STRINGS[lang]
  const parts = risk.horizons.map((h) => `${s.inDays(h.days)}: ${s.level[h.level]}.`)
  const rank: Record<Level, number> = { green: 0, amber: 1, red: 2 }
  const worst = [...risk.horizons].sort((a, b) => rank[b.level] - rank[a.level])[0]
  if (worst && worst.level !== 'green' && worst.reasons.length > 0) {
    parts.push(`${s.why}: ${worst.reasons.map((r) => reasonText(r, lang)).join('. ')}.`)
  }
  return `${s.field}, ${risk.district}. ${parts.join(' ')}`
}
