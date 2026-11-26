import type { SubfieldEntry } from './api'
import type { Lang } from './i18n'
export function patchSummary(entry: SubfieldEntry, lang: Lang): string {
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
