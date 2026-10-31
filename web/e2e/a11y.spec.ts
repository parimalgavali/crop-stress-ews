import AxeBuilder from "@axe-core/playwright";
import { expect, test, type Page } from "@playwright/test";

test.beforeEach(async ({ page }) => {
  await page.addInitScript(() => localStorage.setItem('cropews-intro-seen', '1'))
})

// WCAG 2.1 A/AA automated checks on each screen (ADR 0033). The map canvas is excluded: it
// is a picture of the fields, and every field is also in the "Field" list.
const square = (x: number) => ({
  type: "Polygon",
  coordinates: [
    [
      [x, 51.5],
      [x + 0.01, 51.5],
      [x + 0.01, 51.51],
      [x, 51.51],
      [x, 51.5],
    ],
  ],
});
const fields = {
  type: "FeatureCollection",
  features: [
    {
      type: "Feature",
      id: "f2",
      geometry: square(8.1),
      properties: {
        field_id: "f2",
        district: "Soest",
        area_ha: 5.0,
        level: "red",
      },
    },
  ],
};
const reasons = [
  {
    code: "behind_neighbours",
    text_en: "Crop is behind neighbouring fields",
    text_de: "Bestand liegt hinter den Nachbarfeldern",
  },
];
const horizons = [
  { days: 7, risk: 0.03, level: "green", reasons },
  { days: 14, risk: 0.07, level: "amber", reasons },
  { days: 21, risk: 0.3, level: "red", reasons },
];
const live = {
  as_of: "2026-05-04",
  attribution: "test",
  fields: {
    type: "FeatureCollection",
    features: [
      {
        type: "Feature",
        id: "LWK-1",
        geometry: square(8.0),
        properties: {
          field_id: "LWK-1",
          district: "Soest",
          area_ha: 4,
          declared_crop: "Winterweizen",
          level: "red",
          wheat_p: 0.9,
        },
      },
    ],
  },
  conditions: {
    "LWK-1": {
      s2_date: "2026-05-01",
      s2_days_ago: 3,
      ndvi: 0.7,
      ndvi_change: -0.1,
      s1_days_ago: 1,
      vv_change_db: 1.5,
      rain_30d_mm: 12,
      tmean_7d_c: 12,
      tmin_7d_c: 3,
    },
  },
  forecast: {
    Soest: {
      fc_to: "2026-05-09",
      fc_rain_5d_mm: 2,
      fc_tmin_5d_c: 5,
      fc_frost_days: 0,
    },
  },
  risk: {
    "LWK-1": {
      field_id: "LWK-1",
      year: 2026,
      date: "2026-05-04",
      district: "Soest",
      horizons,
    },
  },
  season: {
    fields: {
      "LWK-1": [
        ["2026-04-01", 0.5],
        ["2026-05-01", 0.7],
      ],
    },
    peers: {
      Soest: [
        ["2026-04-01", 0.5],
        ["2026-05-01", 0.75],
      ],
    },
    peer_kind: "cereal",
  },
  phenology: { Soest: { stage: "stem", date: "2026-04-20", n: 3, of: 4 } },
  soil: {
    "LWK-1": {
      soil_type: "Pseudogley",
      texture: "sandiger Lehm",
      nfk_mm: 109,
      gw_level: 0,
      sw_level: 3,
    },
  },
};

test.beforeEach(async ({ page }) => {
  await page.route("https://tile.openstreetmap.org/**", (r) => r.abort());
  await page.route("**/api/dates?*", (r) =>
    r.fulfill({ json: ["2024-05-05"] }),
  );
  await page.route("**/api/fields?*", (r) => r.fulfill({ json: fields }));
  await page.route("**/api/fields/*/risk?*", (r) =>
    r.fulfill({
      json: {
        field_id: "f2",
        year: 2024,
        date: "2024-05-05",
        district: "Soest",
        horizons,
      },
    }),
  );
  await page.route("**/live/latest.json", (r) => r.fulfill({ json: live }));
});

async function expectNoViolations(page: Page) {
  const { violations } = await new AxeBuilder({ page })
    .withTags(["wcag2a", "wcag2aa", "wcag21a", "wcag21aa"])
    .exclude(".maplibregl-canvas")
    .analyze();
  if (process.env.AXE_DEBUG)
    console.log(
      "AXE",
      JSON.stringify(
        violations.map((v) => [
          v.id,
          v.impact,
          v.nodes.map((n) => [
            n.target.join(" "),
            n.failureSummary?.split("\n")[1],
          ]),
        ]),
      ),
    );
  expect(
    violations.map(
      (v) => `${v.id}: ${v.nodes.map((n) => n.target.join(" ")).join(", ")}`,
    ),
  ).toEqual([]);
}

for (const lang of ["EN", "DE"] as const) {
  test(`${lang}: replay card has no WCAG A/AA violations`, async ({ page }) => {
    await page.goto("/");
    await page.getByRole("button", { name: lang, exact: true }).click();
    await page
      .getByLabel(lang === "EN" ? "Field" : "Feld", { exact: true })
      .selectOption("f2");
    await expect(page.locator(".card").first()).toBeVisible();
    await expectNoViolations(page);
  });

  test(`${lang}: live card has no WCAG A/AA violations`, async ({ page }) => {
    await page.goto("/");
    await page.getByRole("button", { name: lang, exact: true }).click();
    await page
      .getByRole("button", { name: lang === "EN" ? "Live" : "Aktuell" })
      .click();
    await page
      .getByLabel(lang === "EN" ? "Field" : "Feld", { exact: true })
      .selectOption("LWK-1");
    await expect(page.getByTestId("live-lines")).toBeVisible();
    await expectNoViolations(page);
  });
}
