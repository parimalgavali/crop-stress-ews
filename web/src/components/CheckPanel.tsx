import { useState } from "react";
import type { Conditions, LiveSeason } from "../api";
import { checkField, validate } from "../checkField";
import { CHECK_STRINGS, nearestWeather } from "../checkStrings";
import type { Lang } from "../i18n";
import { LiveCard } from "./LiveCard";

interface Props {
  lang: Lang;
  live: LiveSeason | null;
  draft: [number, number][] | null;
  setDraft: (d: [number, number][] | null) => void;
  run?: typeof checkField;
}

export function CheckPanel({
  lang,
  live,
  draft,
  setDraft,
  run = checkField,
}: Props) {
  const c = CHECK_STRINGS[lang];
  const [state, setState] = useState<
    | { kind: "idle" }
    | { kind: "loading" }
    | { kind: "problem"; text: string }
    | { kind: "done"; cond: Conditions; note: string }
  >({ kind: "idle" });

  const finish = async () => {
    if (!draft || draft.length < 3) return;
    const ring = [...draft, draft[0]];
    const problem = validate(ring);
    setDraft(null);
    if (problem) return setState({ kind: "problem", text: c.problem[problem] });
    setState({ kind: "loading" });
    try {
      const sat = await run(ring);
      if (!sat.s2_date && !sat.s1_date)
        return setState({ kind: "problem", text: c.problem["no-data"] });
      const near = nearestWeather(ring, live);
      setState({
        kind: "done",
        cond: { ...near?.weather, ...sat } as Conditions,
        note: near ? c.weatherFrom(near.km) : c.noWeather,
      });
    } catch {
      setState({ kind: "problem", text: c.failed });
    }
  };

  if (draft)
    return (
      <section className="card check" aria-label={c.check}>
        <p>{c.howTo}</p>
        <p data-testid="corners">{c.corners(draft.length)}</p>
        <div className="check-buttons">
          <button
            type="button"
            className="big-button"
            onClick={() => setDraft(draft.slice(0, -1))}
            disabled={!draft.length}
          >
            <span aria-hidden="true">↶</span> {c.undo}
          </button>
          <button
            type="button"
            className="big-button"
            onClick={() => setDraft(null)}
          >
            <span aria-hidden="true">✕</span> {c.cancel}
          </button>
          <button
            type="button"
            className="big-button"
            onClick={finish}
            disabled={draft.length < 3}
          >
            <span aria-hidden="true">✓</span> {c.done}
          </button>
        </div>
      </section>
    );

  return (
    <>
      <button
        type="button"
        className="big-button"
        onClick={() => {
          setState({ kind: "idle" });
          setDraft([]);
        }}
      >
        <span aria-hidden="true">✎</span> {c.check}
      </button>
      {state.kind === "loading" && <p role="status">{c.loading}</p>}
      {state.kind === "problem" && <p role="alert">{state.text}</p>}
      {state.kind === "done" && (
        <>
          <LiveCard
            cond={state.cond}
            crop=""
            district={c.yourField}
            lang={lang}
          />
          <p className="hint">{state.note}</p>
        </>
      )}
    </>
  );
}
