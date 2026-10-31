import type {
  Conditions,
  Forecast,
  Scoreboard,
  SeriesPoint,
  WinterCheck,
  Phenology,
  Soil,
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
/** Soil-moisture change worth mentioning, m³/m³ (about the 10 %/90 % of spring days, ADR 0031). */
export const SM_CHANGE = 0.02;

/** Frost below this on bare ground can damage even hardened winter wheat (ADR 0035). */
export const HARD_FROST_C = -8;
/** Snowfall in the forecast window that counts as a protective cover (ADR 0035). */
export const SNOW_CM = 1;

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
    stage: {
      sown: "sown",
      emerged: "came up",
      stem: "stem growth started",
      heading: "ears appearing",
      yellow: "turning yellow",
      ripe: "ripe",
      harvest: "harvested",
    } as Record<Phenology["stage"], string>,
    soil: (kind: string) => `Soil (NRW soil map): ${kind}`,
    holds: {
      little: "holds little water, dries out fast",
      medium: "holds a medium amount of water",
      lots: "holds a lot of water",
    } as Record<WaterHold, string>,
    groundwater: "groundwater close to the surface",
    stauwet: "tends to stay wet after rain",
    pheno: (stage: string, k: number, n: number, d: string, km: number) =>
      `Winter wheat around here: ${stage} (${k} of ${n} DWD observers within ${km} km, first on ${d})`,
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
    soilDrying: "soil drying out",
    soilWetting: "soil getting wetter",
    scoreNone:
      "Forecast check: none checked yet. Every forecast is saved before the outcome is known and checked later.",
    scoreSome: (n: number, hits: number, onsets: number) =>
      `Forecast check: ${n} forecasts checked so far. A red alarm came before ${hits} of ${onsets} stress events (14 days ahead).`,
    forecastFrost: (n: number) =>
      `frost on ${n} ${n === 1 ? "night" : "nights"}`,
    frostSnow: "snow expected — that protects the crop",
    frostBare: "on bare ground",
    frostHardBare: "hard frost on bare ground — worth watching",
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
    photoShow: "Show satellite photo of this field",
    photoLoading: "Loading satellite photo…",
    photoAlt: (d: string) => `Satellite photo of this field on ${d}, true colours, cut to the field border`,
    photoCaption: (d: string) => `Satellite photo of ${d} (Copernicus Sentinel-2). Green is crop, brown is bare soil.`,
    photoNone: "No satellite photo found for this date.",
    photoError: "The satellite photo could not be loaded. Check the internet connection and try again.",
    alert:
      "Get a message when this field turns red (free ntfy app, no sign-up)",
    fieldLink: "🔗 Link to this field",
    unknownField:
      "This field is not monitored. Please pick one from the list.",
    linkCopied: "Link copied",
    linkManual: "Copy this link yourself:",
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
    photoShow: "Satellitenfoto dieses Feldes zeigen",
    photoLoading: "Satellitenfoto wird geladen…",
    photoAlt: (d: string) => `Satellitenfoto dieses Feldes vom ${d}, echte Farben, auf die Feldgrenze zugeschnitten`,
    photoCaption: (d: string) => `Satellitenfoto vom ${d} (Copernicus Sentinel-2). Grün ist Bestand, Braun ist offener Boden.`,
    photoNone: "Für dieses Datum wurde kein Satellitenfoto gefunden.",
    photoError: "Das Satellitenfoto konnte nicht geladen werden. Bitte Internetverbindung prüfen und erneut versuchen.",
    alert:
      "Nachricht erhalten, wenn dieses Feld rot wird (kostenlose ntfy-App, ohne Anmeldung)",
    fieldLink: "🔗 Link zu diesem Feld",
    unknownField:
      "Dieses Feld wird nicht beobachtet. Bitte eines aus der Liste wählen.",
    linkCopied: "Link kopiert",
    linkManual: "Diesen Link selbst kopieren:",
    springNote:
      "Stress-Vorhersagen beginnen am 5. April, wenn der Winterweizen wieder wächst.",
    prevCrop: (c: string) => `Angebaute Kultur dieses Jahr: ${c}`,
    stage: {
      sown: "gesät",
      emerged: "aufgelaufen",
      stem: "Schossen hat begonnen",
      heading: "Ähren schieben",
      yellow: "Gelbreife",
      ripe: "reif",
      harvest: "geerntet",
    } as Record<Phenology["stage"], string>,
    soil: (kind: string) => `Boden (Bodenkarte NRW): ${kind}`,
    holds: {
      little: "speichert wenig Wasser, trocknet schnell aus",
      medium: "speichert mittel viel Wasser",
      lots: "speichert viel Wasser",
    } as Record<WaterHold, string>,
    groundwater: "Grundwasser nah an der Oberfläche",
    stauwet: "bleibt nach Regen lange nass (Staunässe)",
    pheno: (stage: string, k: number, n: number, d: string, km: number) =>
      `Winterweizen in der Umgebung: ${stage} (${k} von ${n} DWD-Beobachtern im Umkreis von ${km} km, zuerst am ${d})`,
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
    soilDrying: "Boden trocknet ab",
    soilWetting: "Boden wird feuchter",
    scoreNone:
      "Vorhersage-Kontrolle: noch keine geprüft. Jede Vorhersage wird gespeichert, bevor das Ergebnis bekannt ist, und später geprüft.",
    scoreSome: (n: number, hits: number, onsets: number) =>
      `Vorhersage-Kontrolle: bisher ${n} Vorhersagen geprüft. Vor ${hits} von ${onsets} Stressereignissen gab es einen roten Alarm (14 Tage vorher).`,
    forecastFrost: (n: number) =>
      `Frost in ${n} ${n === 1 ? "Nacht" : "Nächten"}`,
    frostSnow: "Schnee erwartet — der schützt den Bestand",
    frostBare: "auf offenem Boden",
    frostHardBare: "starker Frost auf offenem Boden — lieber nachsehen",
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
export type WaterHold = "little" | "medium" | "lots";

/** Available water capacity in the root zone (nFK, mm), in three plain classes (ADR 0030). */
export function waterHold(nfk: number): WaterHold {
  return nfk < 90 ? "little" : nfk < 200 ? "medium" : "lots";
}

export function soilLine(soil: Soil, lang: Lang): string | null {
  const s = T[lang];
  const kind = [soil.soil_type, soil.texture].filter(Boolean).join(", ");
  if (!kind) return null;
  const notes = [
    soil.nfk_mm != null ? s.holds[waterHold(soil.nfk_mm)] : null,
    soil.gw_level != null && soil.gw_level >= 1 && soil.gw_level <= 3
      ? s.groundwater
      : null,
    soil.sw_level != null && soil.sw_level >= 3 ? s.stauwet : null,
  ].filter((n): n is string => n != null);
  return [s.soil(kind), ...notes].join(" · ");
}

export function conditionLines(
  c: Conditions,
  crop: string,
  lang: Lang,
  wheatP?: number | null,
  fc?: Forecast,
  winter?: WinterCheck,
  pheno?: Phenology,
  soil?: Soil,
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
      fc.fc_frost_days > 0
        ? [
            s.forecastFrost(fc.fc_frost_days),
            (fc.fc_snow_5d_cm ?? 0) >= SNOW_CM
              ? s.frostSnow
              : fc.fc_tmin_5d_c <= HARD_FROST_C
                ? s.frostHardBare
                : s.frostBare,
          ].join(", ")
        : null,
      fc.fc_sm_change_5d == null
        ? null
        : fc.fc_sm_change_5d <= -SM_CHANGE
          ? s.soilDrying
          : fc.fc_sm_change_5d >= SM_CHANGE
            ? s.soilWetting
            : null,
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
  if (pheno)
    lines.push({
      icon: "🌿",
      text: s.pheno(
        s.stage[pheno.stage],
        pheno.at_stage,
        pheno.observers,
        formatDate(pheno.first_date, lang),
        pheno.radius_km,
      ),
    });
  const soilText = soil ? soilLine(soil, lang) : null;
  if (soilText) lines.push({ icon: "🟫", text: soilText });
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
