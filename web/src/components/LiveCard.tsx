import { useEffect, useRef, useState } from "react";
import type {
  Conditions,
  Evidence,
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
import { chartSummary, conditionLines, evidenceLines, LIVE_STRINGS, scoreLine } from "../live";
import { CheckedIt } from "./CheckedIt";
import { lastCheckText } from "../fieldChecks";
import { fieldLink } from "../fieldLink";
import { FieldPhoto } from "./FieldPhoto";
import { ObservationLog } from "./ObservationLog";
import { SeasonChart } from "./SeasonChart";
import { SubfieldMap } from "./SubfieldMap";
import WeatherStrip from "./WeatherStrip";
import { speak } from "../speech";

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
  evidence?: Evidence;
  subfield?: import("../api").SubfieldEntry;
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
  evidence,
  subfield,
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
  const ha = subfield?.zones.reduce((a, z) => a + z.area_ha, 0) ?? 0;
  const subText = subfield
    ? (subfield.zones.length
        ? l.patches?.(subfield.zones.length, Math.round(ha * 10) / 10, subfield.date)
        : l.patchesNone?.(subfield.date)) ?? null
    : null;
  const ev = evidence ? evidenceLines(evidence, lang) : null;
  const [speaking, setSpeaking] = useState(false);
  const [copied, setCopied] = useState(false);
  const canSpeak = typeof window !== "undefined" && "speechSynthesis" in window;

  const stopRef = useRef<(() => void) | null>(null);

  useEffect(
    () => () => {
      stopRef.current?.();
      if (canSpeak) window.speechSynthesis.cancel();
    },
    [canSpeak, cond, lang],
  );

  useEffect(() => setCopied(false), [fieldId]);

  const toggleSpeech = () => {
    if (!canSpeak) return;
    if (speaking) {
      stopRef.current?.();
      return setSpeaking(false);
    }
    window.speechSynthesis.cancel();
    const checked = fieldId ? lastCheckText(fieldId, lang) : null;
    stopRef.current = speak(
      `${notice ? `${notice} ` : ""}${s.field}, ${district}. ${lines.map((x) => x.text).join(". ")}. ${chart ? `${chart}. ` : ""}${spring ? "" : l.springNote} ${ev ? `${ev.label}. ` : ""}${scoreLine(board, lang)}${checked ? ` ${checked}.` : ""}${subText ? ` ${subText}.` : ""}`,
      lang,
      () => {
        stopRef.current = null;
        setSpeaking(false);
      },
    );
    setSpeaking(true);
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
      {fieldId && (
        <CheckedIt key={fieldId} fieldId={fieldId} light={light} lang={lang} />
      )}
      {forecast?.fc_days?.length ? (
        <WeatherStrip days={forecast.fc_days} lang={lang} />
      ) : null}
      <SeasonChart
        series={series}
        peers={peers}
        peerKind={peerKind}
        lang={lang}
      />
      {subfield && <SubfieldMap entry={subfield} lang={lang} />}
      {ring && cond.s2_date && (
        <FieldPhoto
          ring={ring}
          date={cond.s2_date}
          dateLabel={formatDate(cond.s2_date, lang)}
          lang={lang}
        />
      )}
      {ev && (
        <details className="evidence">
          <summary>
            {l.evidenceTitle} — {ev.label}
          </summary>
          <ul>
            {ev.lines.map((x) => (
              <li key={x}>{x}</li>
            ))}
          </ul>
        </details>
      )}
      {!spring && <p className="hint">{l.springNote}</p>}
      {fieldId && (
        <details className="evidence more">
          <summary>{l.moreTitle}</summary>
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
          <div className="more-buttons">
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
            <button
              type="button"
              className="big-button"
              onClick={() => window.print()}
            >
              {l.printReport}
            </button>
          </div>
          {copied && <p role="status">{l.linkCopied}</p>}
          <ObservationLog fieldId={fieldId} lang={lang} />
        </details>
      )}
      {fieldId && (
        <div className="print-only" data-testid="print-report">
          <p className="print-meta">
            Crop Stress EWS · {district} · {fieldId}
            {asOf ? ` · ${l.asOf} ${formatDate(asOf, lang)}` : ""}
          </p>
          <p className="print-meta">{fieldLink(fieldId)}</p>
        </div>
      )}
      <p className="hint" data-testid="scoreboard">
        {scoreLine(board, lang)}
      </p>
    </section>
  );
}
