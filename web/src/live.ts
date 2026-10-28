import type { Conditions } from "./api";
import { formatDate, type Lang } from "./i18n";

export type Greenness = "bare" | "some" | "green";
export type Trend = "up" | "down" | "steady";

export const greenness = (ndvi: number): Greenness =>
  ndvi < 0.3 ? "bare" : ndvi < 0.6 ? "some" : "green";
export const trend = (change: number | null | undefined): Trend | null =>
  change == null
    ? null
    : change > 0.05
      ? "up"
      : change < -0.05
        ? "down"
        : "steady";
export const radarChanged = (db: number | null | undefined) =>
  db != null && Math.abs(db) >= 2;

const T = {
  en: {
    live: "Live",
    asOf: "Data as of",
    title: "Conditions now",
    springNote:
      "Stress forecasts start on 5 April, when winter wheat starts growing again.",
    prevCrop: (c: string) => `Crop declared this year: ${c}`,
    image: (d: number, date: string) =>
      `Last clear satellite image: ${d} days ago (${date})`,
    noImage: "No clear satellite image recently (clouds)",
    green: {
      bare: "Mostly bare soil",
      some: "Some green cover",
      green: "Green crop cover",
    } as Record<Greenness, string>,
    trend: {
      up: "getting greener",
      down: "getting less green",
      steady: "no big change",
    } as Record<Trend, string>,
    radar: (d: number) => `Radar image: ${d} days ago`,
    radarChange: "Radar shows a change on the field",
    radarSame: "Radar shows no big change",
    rain: (mm: number) => `Rain in the last 30 days: ${Math.round(mm)} mm`,
    temp: (m: number, lo: number) =>
      `Last 7 days: ${m.toFixed(0)} °C on average, lowest ${lo.toFixed(0)} °C`,
    frost: "Frost",
    noLive: "Live data is not available right now.",
  },
  de: {
    live: "Aktuell",
    asOf: "Daten vom",
    title: "Zustand jetzt",
    springNote:
      "Stress-Vorhersagen beginnen am 5. April, wenn der Winterweizen wieder wächst.",
    prevCrop: (c: string) => `Angebaute Kultur dieses Jahr: ${c}`,
    image: (d: number, date: string) =>
      `Letztes klares Satellitenbild: vor ${d} Tagen (${date})`,
    noImage: "Zuletzt kein klares Satellitenbild (Wolken)",
    green: {
      bare: "Meist offener Boden",
      some: "Etwas grüner Bewuchs",
      green: "Grüner Bestand",
    } as Record<Greenness, string>,
    trend: {
      up: "wird grüner",
      down: "wird weniger grün",
      steady: "kaum Veränderung",
    } as Record<Trend, string>,
    radar: (d: number) => `Radarbild: vor ${d} Tagen`,
    radarChange: "Radar zeigt eine Veränderung auf dem Feld",
    radarSame: "Radar zeigt kaum Veränderung",
    rain: (mm: number) => `Regen in den letzten 30 Tagen: ${Math.round(mm)} mm`,
    temp: (m: number, lo: number) =>
      `Letzte 7 Tage: im Mittel ${m.toFixed(0)} °C, tiefster Wert ${lo.toFixed(0)} °C`,
    frost: "Frost",
    noLive: "Aktuelle Daten sind gerade nicht verfügbar.",
  },
};
export const LIVE_STRINGS = T;

export interface Line {
  icon: string;
  text: string;
}

/** Plain-language lines for one field; the same lines are read aloud. */
export function conditionLines(
  c: Conditions,
  crop: string,
  lang: Lang,
): Line[] {
  const s = T[lang];
  const lines: Line[] = [];
  if (c.s2_date != null && c.s2_days_ago != null && c.ndvi != null) {
    lines.push({
      icon: "🛰",
      text: s.image(c.s2_days_ago, formatDate(c.s2_date, lang)),
    });
    const t = trend(c.ndvi_change);
    lines.push({
      icon: "🌱",
      text: `${s.green[greenness(c.ndvi)]}${t ? `, ${s.trend[t]}` : ""}`,
    });
  } else lines.push({ icon: "☁", text: s.noImage });
  if (c.s1_days_ago != null) {
    lines.push({
      icon: "📡",
      text: `${s.radar(c.s1_days_ago)} · ${radarChanged(c.vv_change_db) ? s.radarChange : s.radarSame}`,
    });
  }
  if (c.rain_30d_mm != null)
    lines.push({ icon: "🌧", text: s.rain(c.rain_30d_mm) });
  if (c.tmean_7d_c != null && c.tmin_7d_c != null) {
    lines.push({
      icon: c.tmin_7d_c < 0 ? "❄" : "🌡",
      text: `${s.temp(c.tmean_7d_c, c.tmin_7d_c)}${c.tmin_7d_c < 0 ? ` · ${s.frost}` : ""}`,
    });
  }
  lines.push({ icon: "🌾", text: s.prevCrop(crop) });
  return lines;
}
