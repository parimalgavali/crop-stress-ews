export type Ring = [number, number][];

const A = 6378137;
const F = 1 / 298.257223563;
const K0 = 0.9996;

/** WGS84 lon/lat to UTM (northern hemisphere) easting/northing in metres. */
export function toUtm(
  lon: number,
  lat: number,
  zone: number,
): [number, number] {
  const e2 = F * (2 - F);
  const ep2 = e2 / (1 - e2);
  const phi = (lat * Math.PI) / 180;
  const lam0 = (((zone - 1) * 6 - 180 + 3) * Math.PI) / 180;
  const lam = (lon * Math.PI) / 180;
  const n = A / Math.sqrt(1 - e2 * Math.sin(phi) ** 2);
  const t = Math.tan(phi) ** 2;
  const c = ep2 * Math.cos(phi) ** 2;
  const a = Math.cos(phi) * (lam - lam0);
  const m =
    A *
    ((1 - e2 / 4 - (3 * e2 ** 2) / 64 - (5 * e2 ** 3) / 256) * phi -
      ((3 * e2) / 8 + (3 * e2 ** 2) / 32 + (45 * e2 ** 3) / 1024) *
        Math.sin(2 * phi) +
      ((15 * e2 ** 2) / 256 + (45 * e2 ** 3) / 1024) * Math.sin(4 * phi) -
      ((35 * e2 ** 3) / 3072) * Math.sin(6 * phi));
  const x =
    K0 *
      n *
      (a +
        ((1 - t + c) * a ** 3) / 6 +
        ((5 - 18 * t + t ** 2 + 72 * c - 58 * ep2) * a ** 5) / 120) +
    500000;
  const y =
    K0 *
    (m +
      n *
        Math.tan(phi) *
        (a ** 2 / 2 +
          ((5 - t + 9 * c + 4 * c ** 2) * a ** 4) / 24 +
          ((61 - 58 * t + t ** 2 + 600 * c - 330 * ep2) * a ** 6) / 720));
  return [x, y];
}

export function pointInRing([x, y]: [number, number], ring: Ring): boolean {
  let inside = false;
  for (let i = 0, j = ring.length - 1; i < ring.length; j = i++) {
    const [xi, yi] = ring[i];
    const [xj, yj] = ring[j];
    if (yi > y !== yj > y && x < ((xj - xi) * (y - yi)) / (yj - yi) + xi)
      inside = !inside;
  }
  return inside;
}

/** Area in hectares of a ring given in metres (shoelace). */
export function areaHa(ring: Ring): number {
  let s = 0;
  for (let i = 0, j = ring.length - 1; i < ring.length; j = i++)
    s += ring[j][0] * ring[i][1] - ring[i][0] * ring[j][1];
  return Math.abs(s) / 2 / 10000;
}

export function median(values: number[]): number | undefined {
  if (values.length === 0) return undefined;
  const v = [...values].sort((a, b) => a - b);
  const mid = v.length >> 1;
  return v.length % 2 ? v[mid] : (v[mid - 1] + v[mid]) / 2;
}
