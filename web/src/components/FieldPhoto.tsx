import { useEffect, useRef, useState } from "react";
import { fieldPhoto, type Photo } from "../fieldPhoto";
import type { Ring } from "../geo";
import { photoExplanation, photoMetadata } from "../photoText";
import { formatDate, type Lang } from "../i18n";
import { LIVE_STRINGS } from "../live";

interface Props {
  ring: Ring;
  date: string;
  dateLabel: string;
  lang: Lang;
  load?: typeof fieldPhoto;
  onDescription?: (text: string) => void;
}

type State =
  | { kind: "idle" }
  | { kind: "loading" }
  | { kind: "done"; photo: Photo }
  | { kind: "problem"; text: string };

/** On request: the field's true-colour Sentinel-2 photo of its last clear date (ADR 0028). */
export function FieldPhoto({ ring, date, lang, load = fieldPhoto, onDescription }: Props) {
  const l = LIVE_STRINGS[lang];
  const [state, setState] = useState<State>({ kind: "idle" });
  const canvas = useRef<HTMLCanvasElement>(null);
  const key = `${date}|${ring.flat().join(",")}`;

  const request = useRef(0);
  const currentKey = useRef(key);
  currentKey.current = key;
  useEffect(() => { request.current++; setState({ kind: "idle" }); return () => { request.current++; }; }, [key]);
  useEffect(() => {
    onDescription?.(`${state.kind === "done" ? photoMetadata(state.photo, lang) : ""} ${photoExplanation(lang)}`);
  }, [state, lang, onDescription]);

  useEffect(() => {
    if (state.kind !== "done" || !canvas.current) return;
    const ctx = canvas.current.getContext("2d");
    const { width, height, rgba } = state.photo;
    ctx?.putImageData(new ImageData(new Uint8ClampedArray(rgba), width, height), 0, 0);
  }, [state]);

  const show = async () => {
    const token = ++request.current;
    const requestedKey = key;
    setState({ kind: "loading" });
    try {
      const photo = await load(ring, date);
      if (token !== request.current || requestedKey !== currentKey.current) return;
      setState(photo ? { kind: "done", photo } : { kind: "problem", text: l.photoNone });
    } catch {
      if (token !== request.current || requestedKey !== currentKey.current) return;
      setState({ kind: "problem", text: l.photoError });
    }
  };

  if (state.kind === "done") {
    const { width, height } = state.photo;
    return (
      <figure className="field-photo" data-testid="field-photo">
        <canvas
          ref={canvas}
          width={width}
          height={height}
          role="img"
          aria-label={l.photoAlt(formatDate(state.photo.date, lang))}
        />
        <figcaption className="hint">{photoMetadata(state.photo, lang)}</figcaption>
        <p className="hint">{photoExplanation(lang)}</p>
      </figure>
    );
  }
  return (
    <>
      <button
        type="button"
        className="big-button"
        onClick={show}
        disabled={state.kind === "loading"}
      >
        <span aria-hidden="true">🛰</span>{" "}
        {state.kind === "loading" ? l.photoLoading : l.photoShow}
      </button>
      <p className="hint">{photoExplanation(lang)}</p>
      {state.kind === "problem" && <p role="alert">{state.text}</p>}
    </>
  );
}
