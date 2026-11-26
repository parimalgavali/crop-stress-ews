import type { Photo } from './fieldPhoto'
import type { Lang } from './i18n'
export function photoExplanation(lang: Lang): string {
  return lang === 'de'
    ? 'Copernicus Sentinel-2: etwa 10 Meter pro Quellpixel. Wolkenfrei bedeutet nicht detailreich. Einzelne Blätter oder kleine Schäden sind nicht erkennbar. Karierte Flächen liegen außerhalb des dargestellten Feldes oder haben keine Bilddaten. Braune Farbe allein bestimmt kein Bestandsproblem.'
    : 'Copernicus Sentinel-2: about 10 metres per source pixel. Clear of clouds does not mean a detailed close-up. Individual leaves or small damage cannot be seen. Checkerboard areas are outside the displayed field or have no image data. Brown colour alone does not identify a crop problem.'
}
export function photoMetadata(photo: Photo, lang: Lang): string {
  const effective = photo.pixel_size_m
  const grid = effective == null ? (lang === 'de' ? 'Ausgaberaster unbekannt' : 'Output grid unknown')
    : lang === 'de' ? `Ausgaberaster etwa ${effective.toLocaleString('de', { maximumFractionDigits: 1 })} Meter pro Pixel${effective > 10 ? ' — für dieses große Feld gröber ausgelesen' : ''}`
      : `Output grid about ${effective.toLocaleString('en', { maximumFractionDigits: 1 })} metres per pixel${effective > 10 ? ' — read at coarser detail for this large field' : ''}`
  return `${photo.date} · Copernicus Sentinel-2 · ${grid}.`
}
