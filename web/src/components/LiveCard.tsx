import { useEffect, useState } from "react";
import type {
  Conditions,
  Forecast,
  Scoreboard,
  SeriesPoint,
  WinterCheck,
} from "../api";
import type { Ring } from "../geo";
import { formatDate, STRINGS, type Lang } from "../i18n";
import { chartSummary, conditionLines, LIVE_STRINGS, scoreLine } from "../live";
import { FieldPhoto } from "./FieldPhoto";
import { SeasonChart } from "./SeasonChart";

interface Props {
  cond: Conditions;
  crop: string;
  district: string;
  lang: Lang;
  wheatP?: number | null;
  forecast?: Forecast;
  board?: Scoreboard | null;
  spring?: boolean;
  alertTopic?: string;
  notice?: string | null;
  winter?: WinterCheck;
  series?: SeriesPoint[];
  peers?: SeriesPoint[];
  peerKind?: "cereal" | "all";
  ring?: Ring | null;
}

export function LiveCard({
  cond,
  crop,
  district,
  lang,
  wheatP,
  forecast,
  board,
  spring = false,
  alertTopic,
  notice,
  winter,
  series,
  peers,
  peerKind,
  ring,
}: Props) {
  const s = STRINGS[lang];
  const l = LIVE_STRINGS[lang];
  const lines = conditionLines(cond, crop, lang, wheatP, forecast, winter);
  const chart = chartSummary(series, peers, lang);
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
      `${notice ? `${notice} ` : ""}${s.field}, ${district}. ${lines.map((x) => x.text).join(". ")}. ${chart ? `${chart}. ` : ""}${spring ? "" : l.springNote} ${scoreLine(board, lang)}`,
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
      <SeasonChart
        series={series}
        peers={peers}
        peerKind={peerKind}
        lang={lang}
      />
      {ring && cond.s2_date && (
        <FieldPhoto
          ring={ring}
          date={cond.s2_date}
          dateLabel={formatDate(cond.s2_date, lang)}
          lang={lang}
        />
      )}
      {!spring && <p className="hint">{l.springNote}</p>}
      {alertTopic && (
        <p>
          <a
            href={`https://ntfy.sh/${alertTopic}`}
            target="_blank"
            rel="noreferrer"
          >
            🔔 {l.alert}
          </a>
        </p>
      )}
      <p className="hint" data-testid="scoreboard">
        {scoreLine(board, lang)}
      </p>
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
