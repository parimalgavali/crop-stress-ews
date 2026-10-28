import { useEffect, useState } from "react";
import type { Conditions } from "../api";
import { STRINGS, type Lang } from "../i18n";
import { conditionLines, LIVE_STRINGS } from "../live";

interface Props {
  cond: Conditions;
  crop: string;
  district: string;
  lang: Lang;
}

export function LiveCard({ cond, crop, district, lang }: Props) {
  const s = STRINGS[lang];
  const l = LIVE_STRINGS[lang];
  const lines = conditionLines(cond, crop, lang);
  const [speaking, setSpeaking] = useState(false);
  const canSpeak = typeof window !== "undefined" && "speechSynthesis" in window;

  useEffect(
    () => () => {
      if (canSpeak) window.speechSynthesis.cancel();
    },
    [canSpeak, cond, lang],
  );

  const toggleSpeech = () => {
    if (!canSpeak) return;
    window.speechSynthesis.cancel();
    if (speaking) return setSpeaking(false);
    const u = new SpeechSynthesisUtterance(
      `${s.field}, ${district}. ${lines.map((x) => x.text).join(". ")}. ${l.springNote}`,
    );
    u.lang = lang === "de" ? "de-DE" : "en-GB";
    u.rate = 0.9;
    u.onend = () => setSpeaking(false);
    setSpeaking(true);
    window.speechSynthesis.speak(u);
  };

  return (
    <section
      className="card"
      aria-live="polite"
      aria-label={`${s.field} ${district}`}
    >
      <h2 className="live-title">{l.title}</h2>
      <ul className="live-lines" data-testid="live-lines">
        {lines.map((x) => (
          <li key={x.text}>
            <span aria-hidden="true">{x.icon}</span> {x.text}
          </li>
        ))}
      </ul>
      <p className="hint">{l.springNote}</p>
      {canSpeak && (
        <button
          type="button"
          className="big-button speak"
          onClick={toggleSpeech}
        >
          <span aria-hidden="true">{speaking ? "■" : "🔊"}</span>{" "}
          {speaking ? s.stop : s.listen}
        </button>
      )}
    </section>
  );
}
