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
    nextStep: 'What to do next',
    inspect: 'Inspect the field for uneven growth, standing water or visible leaf damage. Record what you find in the field visit record in Live view.',
    lowRiskNote: 'Low risk does not confirm that the crop is healthy. Continue your usual field checks.',
    unknownCause: 'This estimates falling behind nearby wheat fields. It does not identify the cause or recommend treatment.',
    missingRiskNote: 'No forecast is available. This does not mean low risk.',
    nothing: 'Nothing unusual',
    noData: 'No forecast for this day',
    inDays: (d: number) => `Next ${d} days`,
    level: { green: 'Low risk', amber: 'Watch', red: 'High risk' } as Record<Level, string>,
    season: 'Season',
    language: 'Language',
    introTitle: 'How it works',
    introLights: '🟢 looks fine · 🟡 keep watching · 🔴 needs a look',
    introPick: 'Tap a field on the map, or choose it from the list.',
    introListen: '🔊 The card can read everything aloud.',
    introDone: 'Got it',
    introOpen: 'How it works',
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
    nextStep: 'Was Sie als Nächstes tun können',
    inspect: 'Prüfen Sie das Feld auf ungleichmäßigen Wuchs, stehendes Wasser oder sichtbare Blattschäden. Halten Sie Ihre Beobachtungen im Feld-Besuchsprotokoll der Live-Ansicht fest.',
    lowRiskNote: 'Geringes Risiko bestätigt nicht, dass der Bestand gesund ist. Setzen Sie Ihre üblichen Feldkontrollen fort.',
    unknownCause: 'Dies schätzt das Zurückfallen hinter benachbarte Weizenfelder. Es bestimmt weder die Ursache noch empfiehlt es eine Behandlung.',
    missingRiskNote: 'Keine Vorhersage verfügbar. Das bedeutet nicht geringes Risiko.',
    nothing: 'Nichts Auffälliges',
    noData: 'Keine Vorhersage für diesen Tag',
    inDays: (d: number) => `Nächste ${d} Tage`,
    level: { green: 'Geringes Risiko', amber: 'Beobachten', red: 'Hohes Risiko' } as Record<
      Level,
      string
    >,
    season: 'Saison',
    language: 'Sprache',
    introTitle: 'So funktioniert es',
    introLights: '🟢 sieht gut aus · 🟡 beobachten · 🔴 braucht einen Blick',
    introPick: 'Ein Feld auf der Karte antippen oder aus der Liste wählen.',
    introListen: '🔊 Die Karte liest alles vor.',
    introDone: 'Verstanden',
    introOpen: 'So funktioniert es',
  },
}

export const reasonText = (r: Reason, lang: Lang) => (lang === 'de' ? r.text_de : r.text_en)

export function formatDate(iso: string, lang: Lang): string {
  return new Date(`${iso}T00:00:00`).toLocaleDateString(lang === 'de' ? 'de-DE' : 'en-GB', {
    day: 'numeric',
    month: 'long',
  })
}

/** Same next step on the card and in read-aloud; no forecast is never low risk. */
export function riskGuidance(risk: FieldRisk, lang: Lang): string {
  const s = STRINGS[lang]
  if (!risk.horizons.length) return s.missingRiskNote
  return `${risk.horizons.some((h) => h.level !== 'green') ? s.inspect : s.lowRiskNote} ${s.unknownCause}`
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
  return `${s.field}, ${risk.district}. ${parts.join(' ')} ${riskGuidance(risk, lang)}`
}
