import { describe, expect, it } from "vitest";
import { areaHa, median, pointInRing, toUtm } from "./geo";
import { ndviMedian, validate } from "./checkField";

describe("geo", () => {
  it("projects to UTM 32N like pyproj", () => {
    const [x, y] = toUtm(8.1, 51.57, 32);
    expect(x).toBeCloseTo(437624.86, 0);
    expect(y).toBeCloseTo(5713597.93, 0);
    const [x2, y2] = toUtm(6.5, 50.8, 32);
    expect(x2).toBeCloseTo(323834.11, 0);
    expect(y2).toBeCloseTo(5630563.75, 0);
  });
  it("area, point in polygon and median", () => {
    const sq: [number, number][] = [
      [0, 0],
      [100, 0],
      [100, 100],
      [0, 100],
    ];
    expect(areaHa(sq)).toBe(1);
    expect(pointInRing([50, 50], sq)).toBe(true);
    expect(pointInRing([150, 50], sq)).toBe(false);
    expect(median([3, 1, 2, 10])).toBe(2.5);
    expect(median([])).toBeUndefined();
  });
});

describe("checkField helpers", () => {
  const ring = (lon: number, lat: number, d: number): [number, number][] => [
    [lon, lat],
    [lon + d, lat],
    [lon + d, lat + d],
    [lon, lat + d],
    [lon, lat],
  ];
  it("rejects fields outside NRW or of odd size", () => {
    expect(validate(ring(11.5, 48.1, 0.005))).toBe("outside");
    expect(validate(ring(8.1, 51.57, 0.0001))).toBe("too-small");
    expect(validate(ring(8.1, 51.57, 0.5))).toBe("too-large");
    expect(validate(ring(8.1, 51.57, 0.005))).toBeNull();
  });
  it("computes NDVI over clear pixels with the baseline offset", () => {
    const { clear, ndvi } = ndviMedian(
      [4, 4, 9, 0],
      [1500, 1500, 1500, 0],
      [4000, 4000, 4000, 0],
      1000,
    );
    expect(clear).toBeCloseTo(2 / 3);
    expect(ndvi).toBeCloseTo((3000 - 500) / 3500);
  });
});
