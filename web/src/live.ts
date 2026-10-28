import type { Conditions, Forecast, Scoreboard } from "./api";
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

export const WET_5D_MM = 20;

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
    forecast: (mm: number, tmin: number) =>
      `Next 5 days (weather forecast): ${Math.round(mm)} mm rain, lowest ${Math.round(tmin)} °C`,
    forecastWet: "heavy rain expected",
    scoreNone:
      "Forecast check: none checked yet. Every forecast is saved before the outcome is known and checked later.",
    scoreSome: (n: number, hits: number, onsets: number) =>
      `Forecast check: ${n} forecasts checked so far. A red alarm came before ${hits} of ${onsets} stress events (14 days ahead).`,
    forecastFrost: (n: number) =>
      `frost on ${n} ${n === 1 ? "night" : "nights"}`,
    temp: (m: number, lo: number) =>
      `Last 7 days: ${m.toFixed(0)} °C on average, lowest ${lo.toFixed(0)} °C`,
    frost: "Frost",
    wheat: (yes: boolean, sure: number) =>
      `${yes ? "Probably winter wheat" : "Probably not winter wheat"} (${sure}% sure, satellite guess)`,
    noLive: "Live data is not available right now.",
    alert:
      "Get a message when this field turns red (free ntfy app, no sign-up)",
  },
  de: {
    live: "Aktuell",
    asOf: "Daten vom",
    title: "Zustand jetzt",
    alert:
      "Nachricht erhalten, wenn dieses Feld rot wird (kostenlose ntfy-App, ohne Anmeldung)",
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
    forecast: (mm: number, tmin: number) =>
      `Nächste 5 Tage (Wettervorhersage): ${Math.round(mm)} mm Regen, tiefstens ${Math.round(tmin)} °C`,
    forecastWet: "viel Regen erwartet",
    scoreNone:
      "Vorhersage-Kontrolle: noch keine geprüft. Jede Vorhersage wird gespeichert, bevor das Ergebnis bekannt ist, und später geprüft.",
    scoreSome: (n: number, hits: number, onsets: number) =>
      `Vorhersage-Kontrolle: bisher ${n} Vorhersagen geprüft. Vor ${hits} von ${onsets} Stressereignissen gab es einen roten Alarm (14 Tage vorher).`,
    forecastFrost: (n: number) =>
      `Frost in ${n} ${n === 1 ? "Nacht" : "Nächten"}`,
    temp: (m: number, lo: number) =>
      `Letzte 7 Tage: im Mittel ${m.toFixed(0)} °C, tiefster Wert ${lo.toFixed(0)} °C`,
    frost: "Frost",
    wheat: (yes: boolean, sure: number) =>
      `${yes ? "Wahrscheinlich Winterweizen" : "Wahrscheinlich kein Winterweizen"} (zu ${sure} % sicher, Schätzung aus Satellitendaten)`,
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
  wheatP?: number | null,
  fc?: Forecast,
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
  if (fc) {
    const notes = [
      fc.fc_rain_5d_mm >= WET_5D_MM ? s.forecastWet : null,
      fc.fc_frost_days > 0 ? s.forecastFrost(fc.fc_frost_days) : null,
    ].filter((n): n is string => n != null);
    lines.push({
      icon: fc.fc_frost_days > 0 ? "❄" : "☔",
      text: [s.forecast(fc.fc_rain_5d_mm, fc.fc_tmin_5d_c), ...notes].join(
        " · ",
      ),
    });
  }
  if (wheatP != null) {
    const yes = wheatP >= 0.5;
    const sure = Math.round(100 * (yes ? wheatP : 1 - wheatP));
    lines.push({ icon: yes ? "🌾" : "❔", text: s.wheat(yes, sure) });
  }
  lines.push({ icon: "🌾", text: s.prevCrop(crop) });
  return lines;
}

export function scoreLine(
  board: Scoreboard | null | undefined,
  lang: Lang,
): string {
  const s = T[lang];
  const h = board?.horizons["14"];
  return h && h.scored > 0
    ? s.scoreSome(h.scored, h.red_hits, h.onsets)
    : s.scoreNone;
}
