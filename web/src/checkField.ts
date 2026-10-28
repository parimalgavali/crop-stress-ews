import { fromUrl } from "geotiff";
import type { Conditions } from "./api";
import { areaHa, median, pointInRing, toUtm, type Ring } from "./geo";

const STAC = "https://planetarycomputer.microsoft.com/api/stac/v1/search";
const SAS = "https://planetarycomputer.microsoft.com/api/sas/v1/token/";
// LWK parcel extent (EPSG:25832) in lon/lat, ADR 0017.
export const NRW_BOUNDS = { west: 5.9, south: 50.3, east: 9.5, north: 52.6 };
export const MIN_HA = 0.5;
export const MAX_HA = 500;
const LOOKBACK_DAYS = 60;
const CLEAR_THRESHOLD = 0.8;
const CHANGE_MIN_GAP_DAYS = 20;
const MAX_S2_SCENES = 12;
const MAX_S1_SCENES = 8;
const DAY = 86400000;

export type CheckProblem = "outside" | "too-small" | "too-large" | "no-data";

export function validate(ring: Ring): CheckProblem | null {
  const inside = ring.every(
    ([x, y]) =>
      x >= NRW_BOUNDS.west &&
      x <= NRW_BOUNDS.east &&
      y >= NRW_BOUNDS.south &&
      y <= NRW_BOUNDS.north,
  );
  if (!inside) return "outside";
  const ha = areaHa(ring.map(([x, y]) => toUtm(x, y, 32)));
  return ha < MIN_HA ? "too-small" : ha > MAX_HA ? "too-large" : null;
}

interface Item {
  properties: Record<string, unknown> & { datetime: string };
  assets: Record<string, { href: string }>;
}

const tokens: Record<string, Promise<string>> = {};
const token = (collection: string) =>
  (tokens[collection] ??= fetch(SAS + collection)
    .then((r) => r.json())
    .then((j: { token: string }) => j.token));

async function search(
  collection: string,
  ring: Ring,
  asOf: Date,
  extra: object = {},
): Promise<Item[]> {
  const start = new Date(asOf.getTime() - LOOKBACK_DAYS * DAY).toISOString();
  const r = await fetch(STAC, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      collections: [collection],
      intersects: { type: "Polygon", coordinates: [ring] },
      datetime: `${start}/${asOf.toISOString()}`,
      sortby: [{ field: "datetime", direction: "desc" }],
      limit: 50,
      ...extra,
    }),
  });
  if (!r.ok) throw new Error(`STAC ${r.status}`);
  return ((await r.json()) as { features: Item[] }).features;
}

/** Pixel values whose centres fall inside the ring, on a grid of `size` metres. */
export async function readInside(
  url: string,
  ring: Ring,
  size: number,
): Promise<number[]> {
  const image = await (await fromUrl(url)).getImage();
  const [ox, oy] = image.getOrigin();
  const [rx, ry] = image.getResolution();
  const xs = ring.map((p) => p[0]);
  const ys = ring.map((p) => p[1]);
  const [minx, maxx, miny, maxy] = [
    Math.min(...xs),
    Math.max(...xs),
    Math.min(...ys),
    Math.max(...ys),
  ];
  const width = Math.max(1, Math.ceil((maxx - minx) / size));
  const height = Math.max(1, Math.ceil((maxy - miny) / size));
  const x0 = Math.floor((minx - ox) / rx);
  const y0 = Math.floor((maxy - oy) / ry);
  const x1 = x0 + Math.ceil((width * size) / rx);
  const y1 = y0 + Math.ceil((height * size) / -ry);
  const [band] = (await image.readRasters({
    window: [x0, y0, x1, y1],
    width,
    height,
  })) as unknown as ArrayLike<number>[];
  const out: number[] = [];
  for (let j = 0; j < height; j++)
    for (let i = 0; i < width; i++) {
      const centre: [number, number] = [
        ox + x0 * rx + (i + 0.5) * size,
        oy + y0 * ry - (j + 0.5) * size,
      ];
      if (pointInRing(centre, ring)) out.push(band[j * width + i]);
    }
  return out;
}

const epsgZone = (item: Item) => Number(item.properties["proj:epsg"]) - 32600;
const daysAgo = (d: string, asOf: Date) =>
  Math.round((asOf.getTime() - new Date(d).getTime()) / DAY);
const isoDay = (d: string) => d.slice(0, 10);

export function ndviMedian(
  scl: number[],
  red: number[],
  nir: number[],
  offset: number,
) {
  const valid = scl.filter((c) => c !== 0).length;
  const clearIdx = scl.flatMap((c, i) => (c === 4 || c === 5 ? [i] : []));
  const clear = valid ? clearIdx.length / valid : 0;
  const ndvi = median(
    clearIdx
      .map((i) => {
        const r = (red[i] - offset) / 1e4;
        const n = (nir[i] - offset) / 1e4;
        return (n - r) / (n + r);
      })
      .filter(Number.isFinite),
  );
  return { clear, ndvi };
}

async function optical(ring: Ring, asOf: Date): Promise<Partial<Conditions>> {
  const items = (
    await search("sentinel-2-l2a", ring, asOf, {
      query: { "eo:cloud_cover": { lt: 90 } },
    })
  ).slice(0, MAX_S2_SCENES);
  const sas = await token("sentinel-2-l2a");
  let latest: { date: string; ndvi: number } | null = null;
  for (const item of items) {
    if (
      latest &&
      daysAgo(latest.date, new Date(item.properties.datetime)) <
        -CHANGE_MIN_GAP_DAYS
    )
      continue;
    const local = ring.map(([x, y]) => toUtm(x, y, epsgZone(item)));
    const scl = await readInside(`${item.assets.SCL.href}?${sas}`, local, 20);
    if (
      scl.filter((c) => c === 4 || c === 5).length /
        Math.max(1, scl.filter((c) => c !== 0).length) <
      CLEAR_THRESHOLD
    )
      continue;
    const [red, nir] = await Promise.all(
      ["B04", "B08"].map((b) =>
        readInside(`${item.assets[b].href}?${sas}`, local, 20),
      ),
    );
    const offset =
      String(item.properties["s2:processing_baseline"] ?? "00.00") >= "04.00"
        ? 1000
        : 0;
    const { ndvi } = ndviMedian(scl, red, nir, offset);
    if (ndvi === undefined) continue;
    const date = isoDay(item.properties.datetime);
    if (!latest) {
      latest = { date, ndvi };
      continue;
    }
    if (daysAgo(date, new Date(latest.date)) >= CHANGE_MIN_GAP_DAYS)
      return {
        s2_date: latest.date,
        s2_days_ago: daysAgo(latest.date, asOf),
        ndvi: latest.ndvi,
        ndvi_change: latest.ndvi - ndvi,
      };
  }
  return latest
    ? {
        s2_date: latest.date,
        s2_days_ago: daysAgo(latest.date, asOf),
        ndvi: latest.ndvi,
        ndvi_change: null,
      }
    : {};
}

async function radar(ring: Ring, asOf: Date): Promise<Partial<Conditions>> {
  const items = (await search("sentinel-1-rtc", ring, asOf)).slice(
    0,
    MAX_S1_SCENES,
  );
  if (items.length === 0) return {};
  const sas = await token("sentinel-1-rtc");
  const views = await Promise.all(
    items.map(async (item) => {
      const local = ring.map(([x, y]) => toUtm(x, y, epsgZone(item)));
      const vv = (
        await readInside(`${item.assets.vv.href}?${sas}`, local, 20)
      ).filter((v) => v > 0);
      const m = median(vv);
      return {
        date: isoDay(item.properties.datetime),
        orbit: item.properties["sat:orbit_state"],
        db: m ? 10 * Math.log10(m) : undefined,
      };
    }),
  );
  const ok = views.filter((v) => v.db !== undefined) as {
    date: string;
    orbit: unknown;
    db: number;
  }[];
  if (ok.length === 0) return {};
  const [last, ...rest] = ok;
  const before = median(
    rest.filter((v) => v.orbit === last.orbit).map((v) => v.db),
  );
  return {
    s1_date: last.date,
    s1_days_ago: daysAgo(last.date, asOf),
    vv_change_db: before === undefined ? null : last.db - before,
  };
}

/** Current Sentinel-2/1 conditions for a drawn field, read in the browser (ADR 0017). */
export async function checkField(
  ring: Ring,
  asOf = new Date(),
): Promise<Conditions> {
  const [o, r] = await Promise.all([optical(ring, asOf), radar(ring, asOf)]);
  return { ...o, ...r };
}
