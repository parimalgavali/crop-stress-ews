import type { Conditions, LiveSeason } from "./api";
import type { CheckProblem } from "./checkField";

const WEATHER_MAX_KM = 15;
const SATELLITE_KEYS = /^(s1_|s2_|ndvi|ndmi|vv_)/;

export const CHECK_STRINGS = {
  en: {
    check: "Check my field",
    howTo: "Tap the corners of your field on the map, then press Done.",
    corners: (n: number) => `Corners: ${n}`,
    undo: "Undo",
    cancel: "Cancel",
    done: "Done",
    loading:
      "Reading the latest satellite images. This can take 10–30 seconds.",
    yourField: "Your field",
    weatherFrom: (km: number) =>
      `Weather from a monitored field ${km.toFixed(0)} km away.`,
    noWeather: "No weather data nearby.",
    problem: {
      outside: "This field is outside North Rhine-Westphalia.",
      "too-small": "This field is too small. Draw at least 0.5 ha.",
      "too-large": "This area is too large. Draw one field, at most 500 ha.",
      "no-data":
        "No satellite images found for this field in the last 60 days.",
    } as Record<CheckProblem, string>,
    failed: "The satellite service did not answer. Please try again later.",
  },
  de: {
    check: "Mein Feld prüfen",
    howTo:
      "Tippen Sie die Ecken Ihres Feldes auf der Karte an und dann auf Fertig.",
    corners: (n: number) => `Ecken: ${n}`,
    undo: "Zurück",
    cancel: "Abbrechen",
    done: "Fertig",
    loading:
      "Die neuesten Satellitenbilder werden gelesen. Das dauert 10–30 Sekunden.",
    yourField: "Ihr Feld",
    weatherFrom: (km: number) =>
      `Wetter von einem beobachteten Feld in ${km.toFixed(0)} km Entfernung.`,
    noWeather: "Keine Wetterdaten in der Nähe.",
    problem: {
      outside: "Dieses Feld liegt außerhalb von Nordrhein-Westfalen.",
      "too-small": "Das Feld ist zu klein. Zeichnen Sie mindestens 0,5 ha.",
      "too-large":
        "Die Fläche ist zu groß. Zeichnen Sie ein Feld mit höchstens 500 ha.",
      "no-data":
        "In den letzten 60 Tagen gibt es keine Satellitenbilder für dieses Feld.",
    } as Record<CheckProblem, string>,
    failed:
      "Der Satellitendienst antwortet nicht. Bitte später erneut versuchen.",
  },
};

const km = ([a, b]: [number, number], [c, d]: [number, number]) => {
  const r = Math.PI / 180;
  const x = (c - a) * r * Math.cos(((b + d) / 2) * r);
  return 6371 * Math.hypot(x, (d - b) * r);
};
const centre = (pts: [number, number][]): [number, number] => [
  pts.reduce((s, p) => s + p[0], 0) / pts.length,
  pts.reduce((s, p) => s + p[1], 0) / pts.length,
];

/** Weather keys of the nearest monitored field within 15 km, and its distance. */
export function nearestWeather(
  ring: [number, number][],
  live: LiveSeason | null,
): { weather: Partial<Conditions>; km: number } | null {
  if (!live) return null;
  const c = centre(ring);
  let best: { id: string; km: number } | null = null;
  for (const f of live.fields.features) {
    const g = f.geometry;
    const outer =
      g.type === "Polygon"
        ? g.coordinates[0]
        : g.type === "MultiPolygon"
          ? g.coordinates[0][0]
          : null;
    if (!outer) continue;
    const d = km(c, centre(outer as [number, number][]));
    if (d <= WEATHER_MAX_KM && (!best || d < best.km))
      best = { id: f.properties.field_id, km: d };
  }
  const cond = best && live.conditions[best.id];
  if (!best || !cond) return null;
  const weather = Object.fromEntries(
    Object.entries(cond).filter(([k]) => !SATELLITE_KEYS.test(k)),
  );
  return { weather: weather as Partial<Conditions>, km: best.km };
}
