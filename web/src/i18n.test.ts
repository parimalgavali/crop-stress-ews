import { describe, expect, it } from "vitest";
import type { FieldRisk } from "./api";
import { speechText } from "./i18n";

const reason = {
  code: "dry_spell",
  text_en: "Little rain in the last 30 days",
  text_de: "Wenig Regen",
};
const risk: FieldRisk = {
  field_id: "a",
  year: 2024,
  date: "2024-05-10",
  district: "Soest",
  horizons: [
    { days: 7, risk: 0.02, level: "green", reasons: [] },
    { days: 14, risk: 0.2, level: "red", reasons: [reason] },
  ],
};

describe("speechText", () => {
  it("reads every horizon and the worst horizon reasons", () => {
    expect(speechText(risk, "en")).toBe(
      "Field, Soest. Next 7 days: Low risk. Next 14 days: High risk. Why: Little rain in the last 30 days.",
    );
  });
  it("speaks German", () => {
    expect(speechText(risk, "de")).toContain(
      "Nächste 14 Tage: Hohes Risiko. Warum: Wenig Regen.",
    );
  });
  it("gives no reason when all is green", () => {
    const calm = { ...risk, horizons: [risk.horizons[0]] };
    expect(speechText(calm, "en")).not.toContain("Why");
  });
});
