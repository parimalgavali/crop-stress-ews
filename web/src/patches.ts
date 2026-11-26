import type { SubfieldEntry } from './api'
import type { Lang } from './i18n'
export function patchSummary(entry: SubfieldEntry | undefined, lang: Lang): string {
  if (!entry) return PATCH_TEXT[lang].unavailable
  const status = entry.assessment?.status
  const date = entry.date
  const ha = Math.round(entry.zones.reduce((a, z) => a + z.area_ha, 0) * 100) / 100
  if (!status || status === 'insufficient') return lang === 'de'
    ? `Nicht genug klare Bilddetails, um ungleichmäßigen Wuchs zu beurteilen (Bild vom ${date}). Dies bestätigt keinen gesunden Bestand.`
    : `Not enough clear detail to assess uneven growth (image from ${date}). This does not confirm a healthy crop.`
  if (status === 'detected') return lang === 'de'
    ? `${entry.zones.length} mögliche Bereiche mit geringerem Pflanzengrün innerhalb dieses Feldes, etwa ${ha} ha (Bild vom ${date}). Bitte vor Ort prüfen; keine Diagnose.`
    : `${entry.zones.length} candidate areas of lower greenness inside this field, about ${ha} ha (image from ${date}). Inspect on the ground; this is not a diagnosis.`
  return lang === 'de'
    ? `Keine großen Bereiche mit ungleichmäßigem Wuchs im nutzbaren Teil dieses Bildes erkannt (vom ${date}). Kleine Probleme können unsichtbar bleiben; dies bestätigt keinen gesunden Bestand.`
    : `No large uneven-growth areas detected in the usable part of this image (from ${date}). Smaller problems can be invisible; this does not confirm a healthy crop.`
}

export const PATCH_TEXT = {
  en: { title: 'Vegetation map inside this field',
    explain: 'This simplified map compares parts of this field with its own middle greenness value. It is not a normal photo or a comparison with other fields.',
    legend: ['· Low greenness', '+ Medium greenness', '● High greenness', '× Candidate uneven-growth area', '— Outside the usable field area or no clear data'],
    detail: 'Analysis uses a 20 m grid and looks for connected areas of at least four pixels (about 0.16 ha). Display squares may combine several pixels. Greenness and candidate areas do not identify a cause or confirm crop health.',
    unavailable: 'No usable patch assessment is available for this field. This does not confirm a healthy crop.',
  },
  de: { title: 'Vegetationskarte innerhalb dieses Feldes',
    explain: 'Diese vereinfachte Karte vergleicht Feldteile mit dem mittleren Pflanzengrün dieses Feldes. Sie ist kein normales Foto und kein Vergleich mit anderen Feldern.',
    legend: ['· Geringes Pflanzengrün', '+ Mittleres Pflanzengrün', '● Hohes Pflanzengrün', '× Möglicher Bereich mit ungleichmäßigem Wuchs', '— Außerhalb der nutzbaren Feldfläche oder keine klaren Daten'],
    detail: 'Die Analyse nutzt ein 20-m-Raster und sucht zusammenhängende Bereiche ab vier Pixeln (etwa 0,16 ha). Anzeigequadrate können mehrere Pixel zusammenfassen. Pflanzengrün und mögliche Bereiche bestimmen weder die Ursache noch bestätigen sie einen gesunden Bestand.',
    unavailable: 'Für dieses Feld liegt keine nutzbare Beurteilung von Teilflächen vor. Dies bestätigt keinen gesunden Bestand.',
  },
}
