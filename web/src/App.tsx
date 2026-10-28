import { useEffect, useMemo, useState } from "react";
import {
  fetchDates,
  fetchFields,
  fetchRisk,
  loadLive,
  loadScoreboard,
  type Scoreboard,
  type FieldCollection,
  type FieldRisk,
  type Level,
  type LiveSeason,
} from "./api";
import { MapView } from "./components/MapView";
import { LiveCard } from "./components/LiveCard";
import { CheckPanel } from "./components/CheckPanel";
import { RiskCard } from "./components/RiskCard";
import { formatDate, STRINGS, type Lang } from "./i18n";
import { outerRing } from "./fieldPhoto";
import { LIVE_STRINGS, staleNotice } from "./live";

const YEARS = [2024, 2025];
const RANK: Record<Level, number> = { green: 0, amber: 1, red: 2 };

function useOnline(): boolean {
  const [online, setOnline] = useState(navigator.onLine);
  useEffect(() => {
    const update = () => setOnline(navigator.onLine);
    window.addEventListener("online", update);
    window.addEventListener("offline", update);
    return () => {
      window.removeEventListener("online", update);
      window.removeEventListener("offline", update);
    };
  }, []);
  return online;
}

export default function App() {
  const [lang, setLang] = useState<Lang>(
    navigator.language.startsWith("de") ? "de" : "en",
  );
  const [year, setYear] = useState(YEARS[0]);
  const [dates, setDates] = useState<string[]>([]);
  const [dateIdx, setDateIdx] = useState(0);
  const [playing, setPlaying] = useState(false);
  const [fields, setFields] = useState<FieldCollection | null>(null);
  const [selected, setSelected] = useState<string | null>(null);
  const [risk, setRisk] = useState<FieldRisk | null>(null);
  const [error, setError] = useState(false);
  const [isLive, setIsLive] = useState(false);
  const [board, setBoard] = useState<Scoreboard | null | undefined>();
  const [live, setLive] = useState<LiveSeason | null>(null);
  const [liveError, setLiveError] = useState(false);
  const [draft, setDraft] = useState<[number, number][] | null>(null);
  const s = STRINGS[lang];
  const l = LIVE_STRINGS[lang];
  const date = dates[dateIdx];
  const shown: FieldCollection | null = isLive
    ? (live?.fields ?? null)
    : fields;
  const online = useOnline();
  const offline = online ? null : l.offline;
  const stale = isLive && live ? staleNotice(live.as_of, lang) : null;
  const liveField = isLive
    ? live?.fields.features.find((f) => f.properties.field_id === selected)
    : undefined;

  useEffect(() => {
    document.documentElement.lang = lang;
  }, [lang]);

  useEffect(() => {
    fetchDates(year)
      .then((d) => {
        setDates(d);
        setDateIdx(0);
      })
      .catch(() => setError(true));
  }, [year]);

  useEffect(() => {
    if (date)
      fetchFields(year, date)
        .then(setFields)
        .catch(() => setError(true));
  }, [year, date]);

  useEffect(() => {
    if (!selected || !date) return setRisk(null);
    fetchRisk(selected, year, date)
      .then(setRisk)
      .catch(() => setRisk(null));
  }, [selected, year, date]);

  useEffect(() => {
    if (isLive && board === undefined) loadScoreboard().then(setBoard);
  }, [isLive, board]);

  useEffect(() => {
    if (isLive && !live)
      loadLive()
        .then(setLive)
        .catch(() => setLiveError(true));
  }, [isLive, live]);

  useEffect(() => {
    if (!playing) return;
    const t = setInterval(() => {
      setDateIdx((i) => {
        if (i + 1 >= dates.length) {
          setPlaying(false);
          return i;
        }
        return i + 1;
      });
    }, 1200);
    return () => clearInterval(t);
  }, [playing, dates.length]);

  const options = useMemo(
    () =>
      [...(shown?.features ?? [])].sort(
        (a, b) =>
          RANK[b.properties.level ?? "green"] -
            RANK[a.properties.level ?? "green"] ||
          a.properties.field_id.localeCompare(b.properties.field_id),
      ),
    [shown],
  );

  return (
    <div className="app">
      <header className="bar">
        <div>
          <h1>{s.title}</h1>
          <p className="subtitle">{s.subtitle}</p>
        </div>
        <div className="toggles">
          <div role="group" aria-label={s.season}>
            <button
              type="button"
              className="chip"
              aria-pressed={isLive}
              onClick={() => {
                setIsLive(true);
                setPlaying(false);
                setSelected(null);
              }}
            >
              {l.live}
            </button>
            {YEARS.map((y) => (
              <button
                key={y}
                type="button"
                className="chip"
                aria-pressed={!isLive && y === year}
                onClick={() => {
                  setIsLive(false);
                  setYear(y);
                  setSelected(null);
                }}
              >
                {y}
              </button>
            ))}
          </div>
          <div role="group" aria-label={s.language}>
            {(["de", "en"] as const).map((l) => (
              <button
                key={l}
                type="button"
                className="chip"
                aria-pressed={l === lang}
                onClick={() => setLang(l)}
              >
                {l.toUpperCase()}
              </button>
            ))}
          </div>
        </div>
      </header>

      <main className="main">
        <MapView
          fields={shown}
          selected={selected}
          onSelect={setSelected}
          draft={isLive ? draft : null}
          onMapClick={
            isLive && draft ? (p) => setDraft([...draft, p]) : undefined
          }
        />
        <aside className="panel">
          {error && <p role="alert">Data not reachable.</p>}
          <label className="field-label" htmlFor="field-select">
            {s.field}
          </label>
          <select
            id="field-select"
            className="big-select"
            value={selected ?? ""}
            onChange={(e) => setSelected(e.target.value || null)}
          >
            <option value="">{s.chooseField}</option>
            {options.map((f, i) => (
              <option key={f.properties.field_id} value={f.properties.field_id}>
                {`${s.field} ${i + 1} · ${f.properties.district} · ${f.properties.area_ha.toFixed(1)} ha${
                  f.properties.level ? ` · ${s.level[f.properties.level]}` : ""
                }`}
              </option>
            ))}
          </select>
          {isLive && liveError && <p role="alert">{l.noLive}</p>}
          {isLive && (
            <CheckPanel
              lang={lang}
              live={live}
              draft={draft}
              setDraft={setDraft}
            />
          )}
          {isLive ? (
            liveField && live?.conditions[liveField.properties.field_id] ? (
              <>
                {live.risk?.[liveField.properties.field_id] && (
                  <RiskCard
                    risk={live.risk[liveField.properties.field_id]}
                    lang={lang}
                  />
                )}
                <LiveCard
                  cond={live.conditions[liveField.properties.field_id]}
                  crop={liveField.properties.declared_crop}
                  district={liveField.properties.district}
                  lang={lang}
                  wheatP={liveField.properties.wheat_p}
                  forecast={live.forecast?.[liveField.properties.district]}
                  board={board}
                  spring={Boolean(live.risk?.[liveField.properties.field_id])}
                  alertTopic={
                    live.risk?.[liveField.properties.field_id]
                      ? `cropews-nrw-${liveField.properties.field_id.toLowerCase()}`
                      : undefined
                  }
                  notice={[offline, stale].filter(Boolean).join(" ") || null}
                  winter={live.winter?.[liveField.properties.field_id]}
                  series={live.season?.fields[liveField.properties.field_id]}
                  peers={live.season?.peers[liveField.properties.district]}
                  peerKind={live.season?.peer_kind}
                  ring={outerRing(liveField.geometry)}
                  pheno={live.phenology?.[liveField.properties.district]}
                  soil={live.soil?.[liveField.properties.field_id]}
                />
              </>
            ) : (
              <p className="hint">{selected ? s.noData : s.pickHint}</p>
            )
          ) : risk ? (
            <RiskCard risk={risk} lang={lang} />
          ) : (
            <p className="hint">{selected ? s.noData : s.pickHint}</p>
          )}
        </aside>
      </main>

      {offline && (
        <p className="hint" role="status" data-testid="offline">
          <span aria-hidden="true">📵</span> {offline}
        </p>
      )}

      {isLive ? (
        <footer className="bar timeline">
          <p>
            {l.asOf}:{" "}
            <strong data-testid="live-date">
              {live ? formatDate(live.as_of, lang) : "–"}
            </strong>
          </p>
          {stale && (
            <p className="hint" role="status" data-testid="live-stale">
              <span aria-hidden="true">⚠</span> {stale}
            </p>
          )}
        </footer>
      ) : (
        <footer className="bar timeline">
          <button
            type="button"
            className="big-button"
            onClick={() => {
              if (!playing && dateIdx + 1 >= dates.length) setDateIdx(0);
              setPlaying(!playing);
            }}
            disabled={dates.length === 0}
          >
            <span aria-hidden="true">{playing ? "❚❚" : "▶"}</span>{" "}
            {playing ? s.pause : s.play}
          </button>
          <label className="slider">
            <span>
              {s.day}:{" "}
              <strong data-testid="current-date">
                {date ? formatDate(date, lang) : "–"}
              </strong>
            </span>
            <input
              type="range"
              min={0}
              max={Math.max(dates.length - 1, 0)}
              value={dateIdx}
              onChange={(e) => {
                setPlaying(false);
                setDateIdx(Number(e.target.value));
              }}
              aria-valuetext={date ? formatDate(date, lang) : undefined}
            />
          </label>
        </footer>
      )}
    </div>
  );
}
