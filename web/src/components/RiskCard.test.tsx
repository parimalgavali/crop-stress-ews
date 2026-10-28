import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";
import type { FieldRisk } from "../api";
import { RiskCard } from "./RiskCard";

const risk: FieldRisk = {
  field_id: "a",
  year: 2024,
  date: "2024-05-10",
  district: "Soest",
  horizons: [
    {
      days: 7,
      risk: 0.02,
      level: "green",
      reasons: [{ code: "x", text_en: "Hidden", text_de: "x" }],
    },
    {
      days: 14,
      risk: 0.08,
      level: "amber",
      reasons: [
        { code: "heat", text_en: "Hot days recently", text_de: "Heiß" },
      ],
    },
    { days: 21, risk: 0.2, level: "red", reasons: [] },
  ],
};

afterEach(() => vi.unstubAllGlobals());

describe("RiskCard", () => {
  it("shows a light with text per horizon and reasons only for non-green", () => {
    render(<RiskCard risk={risk} lang="en" />);
    expect(screen.getByTestId("horizon-7")).toHaveTextContent("Next 7 days");
    expect(screen.getByTestId("horizon-7")).toHaveTextContent("Low risk");
    expect(screen.getByTestId("horizon-14")).toHaveTextContent(
      "Hot days recently",
    );
    expect(screen.getByTestId("horizon-21")).toHaveTextContent("High risk");
    expect(screen.queryByText("Hidden")).not.toBeInTheDocument();
  });

  it("reads aloud in the chosen language", async () => {
    const speak = vi.fn();
    vi.stubGlobal("speechSynthesis", { speak, cancel: vi.fn() });
    vi.stubGlobal(
      "SpeechSynthesisUtterance",
      class {
        lang = "";
        rate = 1;
        onend: (() => void) | null = null;
        constructor(public text: string) {}
      },
    );
    render(<RiskCard risk={risk} lang="de" />);
    await userEvent.click(screen.getByRole("button", { name: /Vorlesen/ }));
    expect(speak).toHaveBeenCalledOnce();
    expect(speak.mock.calls[0][0].lang).toBe("de-DE");
    expect(speak.mock.calls[0][0].text).toContain("Hohes Risiko");
    expect(screen.getByRole("button", { name: /Stopp/ })).toBeInTheDocument();
  });
});
