import { useEffect, useState } from "react";
import type {
  Conditions,
  Level,
  Forecast,
  Phenology,
  Soil,
  SeasonRain,
  Scoreboard,
  SeriesPoint,
  WinterCheck,
} from "../api";
import type { Ring } from "../geo";
import { formatDate, STRINGS, type Lang } from "../i18n";
import { chartSummary, conditionLines, LIVE_STRINGS, scoreLine } from "../live";
import { CheckedIt } from "./CheckedIt";
import { lastCheckText } from "../fieldChecks";
import { fieldLink } from "../fieldLink";
import { FieldPhoto } from "./FieldPhoto";
import { SeasonChart } from "./SeasonChart";
import WeatherStrip from "./WeatherStrip";

interface Props {
  cond: Conditions;
  crop: string;
  district: string;
  lang: Lang;
  wheatP?: number | null;
  forecast?: Forecast;
  seasonRain?: SeasonRain;
  asOf?: string;
  board?: Scoreboard | null;
  spring?: boolean;
  alertTopic?: string;
  notice?: string | null;
  winter?: WinterCheck;
  series?: SeriesPoint[];
  peers?: SeriesPoint[];
  peerKind?: "cereal" | "all";
  ring?: Ring | null;
  pheno?: Phenology;
  soil?: Soil;
  fieldId?: string;
  light?: Level | null;
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
  pheno,
  soil,
  seasonRain,
  asOf,
  fieldId,
  light = null,
}: Props) {
  const s = STRINGS[lang];
  const l = LIVE_STRINGS[lang];
  const lines = conditionLines(
    cond,
    crop,
    lang,
    wheatP,
    forecast,
    winter,
    pheno,
    soil,
    seasonRain,
  );
  const chart = chartSummary(series, peers, lang);
  const [speaking, setSpeaking] = useState(false);
  const [copied, setCopied] = useState(false);
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
    const checked = fieldId ? lastCheckText(fieldId, lang) : null;
    const u = new SpeechSynthesisUtterance(
      `${notice ? `${notice} ` : ""}${s.field}, ${district}. ${lines.map((x) => x.text).join(". ")}. ${chart ? `${chart}. ` : ""}${spring ? "" : l.springNote} ${scoreLine(board, lang)}${checked ? ` ${checked}.` : ""}`,
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
      {forecast?.fc_days?.length ? (
        <WeatherStrip days={forecast.fc_days} lang={lang} />
      ) : null}
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
      {fieldId && (
        <>
          <button
            type="button"
            className="big-button"
            onClick={async () => {
              const url = fieldLink(fieldId);
              try {
                await navigator.clipboard.writeText(url);
                setCopied(true);
              } catch {
                window.prompt(l.linkManual, url);
              }
            }}
          >
            {l.fieldLink}
          </button>
          {copied && <p role="status">{l.linkCopied}</p>}
          <button
            type="button"
            className="big-button"
            onClick={() => window.print()}
          >
            {l.printReport}
          </button>
          <CheckedIt key={fieldId} fieldId={fieldId} light={light} lang={lang} />
          <div className="print-only" data-testid="print-report">
            <p className="print-meta">
              Crop Stress EWS · {district} · {fieldId}
              {asOf ? ` · ${l.asOf} ${formatDate(asOf, lang)}` : ""}
            </p>
            <p className="print-meta">{fieldLink(fieldId)}</p>
          </div>
        </>
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
