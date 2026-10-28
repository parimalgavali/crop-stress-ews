import { fromUrl } from "geotiff";
import { pointInRing, toUtm, type Ring } from "./geo";

const STAC = "https://planetarycomputer.microsoft.com/api/stac/v1/search";
const SAS = "https://planetarycomputer.microsoft.com/api/sas/v1/token/sentinel-2-l2a";
/** Sentinel-2 true-colour (TCI) resolution in metres. */
const SIZE = 10;
/** Fields larger than this are read at a coarser grid so the photo stays small. */
const MAX_SIDE = 160;

export interface Photo {
  date: string;
  width: number;
  height: number;
  /** RGBA, transparent outside the field border. */
  rgba: Uint8ClampedArray;
}

/** Outer ring of a (Multi)Polygon: the largest polygon's exterior. */
export function outerRing(g: GeoJSON.Geometry): Ring | null {
  const polys =
    g.type === "Polygon" ? [g.coordinates] : g.type === "MultiPolygon" ? g.coordinates : [];
  const rings = polys.map((p) => p[0] as Ring).filter((r) => r && r.length >= 4);
  if (!rings.length) return null;
  const span = (r: Ring) =>
    (Math.max(...r.map((p) => p[0])) - Math.min(...r.map((p) => p[0]))) *
    (Math.max(...r.map((p) => p[1])) - Math.min(...r.map((p) => p[1])));
  return rings.reduce((a, b) => (span(b) > span(a) ? b : a));
}

/** Pixels of three 8-bit bands on a grid, alpha 0 where the centre is outside ``ring``. */
export function maskRgb(
  bands: ArrayLike<number>[],
  width: number,
  height: number,
  centre: (i: number, j: number) => [number, number],
  ring: Ring,
): Uint8ClampedArray {
  const out = new Uint8ClampedArray(width * height * 4);
  for (let j = 0; j < height; j++)
    for (let i = 0; i < width; i++) {
      const k = j * width + i;
      const inside = pointInRing(centre(i, j), ring);
      out[4 * k] = bands[0][k];
      out[4 * k + 1] = bands[1][k];
      out[4 * k + 2] = bands[2][k];
      out[4 * k + 3] = inside && bands[0][k] + bands[1][k] + bands[2][k] > 0 ? 255 : 0;
    }
  return out;
}

interface Item {
  properties: Record<string, unknown> & { datetime: string };
  assets: Record<string, { href: string }>;
}

/** True-colour Sentinel-2 view of the field on ``date``, read in the browser (ADR 0028). */
export async function fieldPhoto(ring: Ring, date: string): Promise<Photo | null> {
  const day = new Date(`${date}T00:00:00Z`);
  const next = new Date(day.getTime() + 86400000);
  const r = await fetch(STAC, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      collections: ["sentinel-2-l2a"],
      intersects: { type: "Polygon", coordinates: [ring] },
      datetime: `${day.toISOString()}/${next.toISOString()}`,
      limit: 10,
    }),
  });
  if (!r.ok) throw new Error(`STAC ${r.status}`);
  const items = ((await r.json()) as { features: Item[] }).features;
  if (!items.length) return null;
  const sas = ((await (await fetch(SAS)).json()) as { token: string }).token;
  for (const item of items) {
    const zone = Number(item.properties["proj:epsg"]) - 32600;
    const local = ring.map(([x, y]) => toUtm(x, y, zone));
    const image = await (await fromUrl(`${item.assets.visual.href}?${sas}`)).getImage();
    const [ox, oy] = image.getOrigin();
    const xs = local.map((p) => p[0]);
    const ys = local.map((p) => p[1]);
    const [minx, maxy] = [Math.min(...xs), Math.max(...ys)];
    const side = Math.max(Math.max(...xs) - minx, maxy - Math.min(...ys));
    const size = Math.max(SIZE, side / MAX_SIDE);
    const width = Math.max(1, Math.ceil((Math.max(...xs) - minx) / size));
    const height = Math.max(1, Math.ceil((maxy - Math.min(...ys)) / size));
    const x0 = Math.floor((minx - ox) / SIZE);
    const y0 = Math.floor((oy - maxy) / SIZE);
    if (x0 < 0 || y0 < 0 || x0 >= image.getWidth() || y0 >= image.getHeight()) continue;
    const bands = (await image.readRasters({
      window: [x0, y0, x0 + Math.ceil((width * size) / SIZE), y0 + Math.ceil((height * size) / SIZE)],
      width,
      height,
      samples: [0, 1, 2],
    })) as unknown as ArrayLike<number>[];
    const centre = (i: number, j: number): [number, number] => [
      ox + x0 * SIZE + (i + 0.5) * size,
      oy - y0 * SIZE - (j + 0.5) * size,
    ];
    const rgba = maskRgb(bands, width, height, centre, local);
    if (!rgba.some((v, k) => k % 4 === 3 && v > 0)) continue;
    return { date, width, height, rgba };
  }
  return null;
}
