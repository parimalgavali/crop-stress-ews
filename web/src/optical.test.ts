import { describe, expect, it, vi } from "vitest";
import { optical } from "./checkField";
import type { Ring } from "./geo";

const DAY = 86400000;
const ring: Ring = [
  [8.0, 51.6],
  [8.02, 51.6],
  [8.02, 51.62],
  [8.0, 51.62],
  [8.0, 51.6],
];
const asOf = new Date("2026-10-27T00:00:00Z");
const iso = (daysBack: number, h = 10) =>
  new Date(asOf.getTime() - daysBack * DAY - h * 3600e3).toISOString();

const item = (daysBack: number) => ({
  properties: {
    datetime: iso(daysBack),
    "proj:epsg": 32632,
    "s2:processing_baseline": "04.00",
  },
  assets: {
    SCL: { href: `https://x/scl-${daysBack}` },
    B04: { href: `https://x/b04-${daysBack}` },
    B08: { href: `https://x/b08-${daysBack}` },
  },
});

// clear scene; ndvi chosen per scene so the change is visible
const fakeDeps = (scenes: { daysBack: number; ndvi: number }[]) => ({
  search: vi.fn(async () => scenes.map((s) => item(s.daysBack))),
  token: vi.fn(async () => "tok"),
  toUtm: ((x: number, y: number) => [x, y]) as never,
  epsgZone: (() => 32) as never,
  readInside: vi.fn(async (url: string) => {
    const db = Number(url.match(/-(\d+)\?/)?.[1]);
    const ndvi = scenes.find((s) => s.daysBack === db)!.ndvi;
    if (url.includes("scl")) return new Array(10).fill(4);
    if (url.includes("b04")) return new Array(10).fill(1000 + 2000 * (1 - ndvi));
    return new Array(10).fill(1000 + 2000 * (1 + ndvi));
  }) as never,
});

describe("optical change-scene selection", () => {
  it("uses a >20-day-old clear scene for the change readout", async () => {
    const deps = fakeDeps([
      { daysBack: 0, ndvi: 0.6 },
      { daysBack: 15, ndvi: 0.9 }, // too recent — must be skipped
      { daysBack: 25, ndvi: 0.4 },
    ]);
    const out = await optical(ring, asOf, deps as never);
    expect(out.ndvi_change).toBeCloseTo(0.2, 3);
    expect(out.s2_date).toBe(iso(0).slice(0, 10));
  });

  it("reports no change when only a 15-day-old scene exists", async () => {
    const deps = fakeDeps([
      { daysBack: 0, ndvi: 0.6 },
      { daysBack: 15, ndvi: 0.4 },
    ]);
    const out = await optical(ring, asOf, deps as never);
    expect(out.ndvi).toBeCloseTo(0.6, 3);
    expect(out.ndvi_change).toBeNull();
  });
});
