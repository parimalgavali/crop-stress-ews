import type {
  Conditions,
  Forecast,
  Scoreboard,
  SeriesPoint,
  WinterCheck,
} from "./api";
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

export type Compare = "above" | "same" | "below";
/** NDVI gap to the peer median that counts as a difference (same scale as ``trend``). */
export const COMPARE_NDVI = 0.05;

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
    behind:
      "Winter check: crop is behind neighbouring winter cereal fields. Worth a look (poor emergence?)",
    emerged: "Winter check: crop has come up like neighbouring fields",
    wet: (date: string) =>
      `Winter check: signs of standing water on ${date}, after heavy rain`,
    dry: "Winter check: no signs of standing water in the last 30 days",
    offline:
      "No internet. Showing the last saved data; map background and Check my field need internet.",
    stale: (d: number) =>
      `This data is ${d} days old. The last update may have failed; it is retried every 5 days.`,
    chartTitle: "Greenness since 1 October",
    chartField: "This field",
    chartPeers: (cereal: boolean) =>
      cereal ? "Neighbouring winter cereal fields" : "Other monitored fields nearby",
    chartSummary: (n: number, from: string, to: string) =>
      `Greenness since 1 October: from ${from} to ${to}, on ${n} clear satellite images`,
    chartCompare: {
      above: "greener than the neighbours",
      same: "about as green as the neighbours",
      below: "less green than the neighbours",
    } as Record<Compare, string>,
    alert:
      "Get a message when this field turns red (free ntfy app, no sign-up)",
  },
  de: {
    live: "Aktuell",
    asOf: "Daten vom",
    title: "Zustand jetzt",
    chartTitle: "Pflanzengrün seit 1. Oktober",
    chartField: "Dieses Feld",
    chartPeers: (cereal: boolean) =>
      cereal ? "Benachbarte Wintergetreide-Felder" : "Andere beobachtete Felder in der Nähe",
    chartSummary: (n: number, from: string, to: string) =>
      `Pflanzengrün seit 1. Oktober: von ${from} auf ${to}, auf ${n} klaren Satellitenbildern`,
    chartCompare: {
      above: "grüner als die Nachbarn",
      same: "etwa so grün wie die Nachbarn",
      below: "weniger grün als die Nachbarn",
    } as Record<Compare, string>,
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
    behind:
      "Winter-Check: Bestand liegt hinter benachbarten Wintergetreide-Feldern. Bitte ansehen (schlecht aufgelaufen?)",
    emerged: "Winter-Check: Bestand ist wie auf den Nachbarfeldern aufgelaufen",
    wet: (date: string) =>
      `Winter-Check: Anzeichen von stehendem Wasser am ${date}, nach starkem Regen`,
    dry: "Winter-Check: keine Anzeichen von stehendem Wasser in den letzten 30 Tagen",
    offline:
      "Kein Internet. Angezeigt werden die zuletzt gespeicherten Daten; Kartenhintergrund und „Mein Feld prüfen“ brauchen Internet.",
    stale: (d: number) =>
      `Diese Daten sind ${d} Tage alt. Die letzte Aktualisierung ist vielleicht fehlgeschlagen; sie wird alle 5 Tage wiederholt.`,
  },
};
export const LIVE_STRINGS = T;

/** Live data older than this gets a notice; runs are every 5 days (ADR 0023). */
export const STALE_DAYS = 7;

export function staleNotice(
  asOf: string,
  lang: Lang,
  today: Date = new Date(),
): string | null {
  const days = Math.floor(
    (Date.UTC(today.getFullYear(), today.getMonth(), today.getDate()) -
      Date.parse(`${asOf}T00:00:00Z`)) /
      86_400_000,
  );
  return days > STALE_DAYS ? T[lang].stale(days) : null;
}

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
  winter?: WinterCheck,
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
  if (winter?.emergence)
    lines.push(
      winter.emergence === "behind"
        ? { icon: "⚠", text: s.behind }
        : { icon: "✓", text: s.emerged },
    );
  if (winter?.wet_date)
    lines.push({ icon: "💧", text: s.wet(formatDate(winter.wet_date, lang)) });
  else if (winter && winter.radar_dates > 0)
    lines.push({ icon: "✓", text: s.dry });
  if (crop) lines.push({ icon: "🌾", text: s.prevCrop(crop) });
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

/** Field vs peer median on the latest peer date at or before the field's last clear image. */
export function compareToPeers(
  series: SeriesPoint[],
  peers: SeriesPoint[] | undefined,
): Compare | null {
  const last = series.at(-1);
  const peer = peers?.filter(([d]) => last && d <= last[0]).at(-1);
  if (!last || !peer) return null;
  const gap = last[1] - peer[1];
  return gap > COMPARE_NDVI ? "above" : gap < -COMPARE_NDVI ? "below" : "same";
}

/** One sentence for screen readers and read-aloud; null below 2 clear images. */
export function chartSummary(
  series: SeriesPoint[] | undefined,
  peers: SeriesPoint[] | undefined,
  lang: Lang,
): string | null {
  if (!series || series.length < 2) return null;
  const t = T[lang];
  const fmt = (v: number) =>
    lang === "de" ? v.toFixed(2).replace(".", ",") : v.toFixed(2);
  const base = t.chartSummary(series.length, fmt(series[0][1]), fmt(series.at(-1)![1]));
  const cmp = compareToPeers(series, peers);
  return cmp ? `${base}; ${t.chartCompare[cmp]}` : base;
}
