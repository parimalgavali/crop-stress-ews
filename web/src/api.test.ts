import { describe, expect, it } from "vitest";
import { staticFields, staticRisk, type StaticSeason } from "./api";

const geometry: GeoJSON.Geometry = { type: "Point", coordinates: [8, 51.5] };
const season: StaticSeason = {
  year: 2024,
  attribution: "test",
  dates: ["2024-05-05", "2024-05-10"],
  reasons: { heat: { en: "Hot days recently", de: "Kürzlich heiße Tage" } },
  fields: {
    type: "FeatureCollection",
    features: ["a", "b"].map((id) => ({
      type: "Feature" as const,
      id,
      geometry,
      properties: { field_id: id, district: "Soest", area_ha: 2, level: null },
    })),
  },
  risk: {
    a: {
      "2024-05-05": [
        [7, 0.02, "green", []],
        [14, 0.3, "red", ["heat"]],
        [21, 0.1, "amber", []],
      ],
    },
  },
};

describe("static demo", () => {
  it("marks each field with its worst level on the date", () => {
    const levels = staticFields(season, "2024-05-05").features.map(
      (f) => f.properties.level,
    );
    expect(levels).toEqual(["red", null]);
  });

  it("expands reason codes into both languages", () => {
    const r = staticRisk(season, "a", "2024-05-05");
    expect(r.district).toBe("Soest");
    expect(r.horizons[1]).toEqual({
      days: 14,
      risk: 0.3,
      level: "red",
      reasons: [
        {
          code: "heat",
          text_en: "Hot days recently",
          text_de: "Kürzlich heiße Tage",
        },
      ],
    });
  });

  it("throws when the field has no prediction for the date", () => {
    expect(() => staticRisk(season, "b", "2024-05-05")).toThrow();
  });
});
