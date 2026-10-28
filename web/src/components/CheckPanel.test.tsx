import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { useState } from "react";
import { describe, expect, it, vi } from "vitest";
import { CheckPanel } from "./CheckPanel";

const square = (lon: number, lat: number, d: number): [number, number][] => [
  [lon, lat],
  [lon + d, lat],
  [lon + d, lat + d],
  [lon, lat + d],
];

function Harness({ start, run }: { start: [number, number][]; run: never }) {
  const [draft, setDraft] = useState<[number, number][] | null>(start);
  return (
    <CheckPanel
      lang="en"
      live={null}
      draft={draft}
      setDraft={setDraft}
      run={run}
    />
  );
}

describe("CheckPanel", () => {
  it("shows satellite conditions for a drawn field", async () => {
    const run = vi.fn().mockResolvedValue({
      s2_date: "2026-10-22",
      s2_days_ago: 6,
      ndvi: 0.55,
      ndvi_change: -0.07,
    });
    render(<Harness start={square(8.1, 51.57, 0.004)} run={run as never} />);
    await userEvent.click(screen.getByRole("button", { name: /done/i }));
    expect(await screen.findByTestId("live-lines")).toHaveTextContent(
      "6 days ago",
    );
    expect(screen.getByText("No weather data nearby.")).toBeInTheDocument();
  });
  it("rejects a field outside NRW without calling the satellite service", async () => {
    const run = vi.fn();
    render(<Harness start={square(11.5, 48.1, 0.004)} run={run as never} />);
    await userEvent.click(screen.getByRole("button", { name: /done/i }));
    expect(screen.getByRole("alert")).toHaveTextContent(
      "outside North Rhine-Westphalia",
    );
    expect(run).not.toHaveBeenCalled();
  });
});
