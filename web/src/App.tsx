import { useEffect, useMemo, useState } from "react";
import {
  fetchDates,
  fetchFields,
  fetchRisk,
  loadLive,
  type FieldCollection,
  type FieldRisk,
  type Level,
  type LiveSeason,
} from "./api";
import { MapView } from "./components/MapView";
import { LiveCard } from "./components/LiveCard";
import { RiskCard } from "./components/RiskCard";
import { formatDate, STRINGS, type Lang } from "./i18n";
import { LIVE_STRINGS } from "./live";

const YEARS = [2024, 2025];
const RANK: Record<Level, number> = { green: 0, amber: 1, red: 2 };

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
  const [live, setLive] = useState<LiveSeason | null>(null);
  const [liveError, setLiveError] = useState(false);
  const s = STRINGS[lang];
  const l = LIVE_STRINGS[lang];
  const date = dates[dateIdx];
  const shown: FieldCollection | null = isLive
    ? (live?.fields ?? null)
    : fields;
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
        <MapView fields={shown} selected={selected} onSelect={setSelected} />
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
          {isLive ? (
            liveField && live?.conditions[liveField.properties.field_id] ? (
              <LiveCard
                cond={live.conditions[liveField.properties.field_id]}
                crop={liveField.properties.declared_crop}
                district={liveField.properties.district}
                lang={lang}
              />
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

      {isLive ? (
        <footer className="bar timeline">
          <p>
            {l.asOf}:{" "}
            <strong data-testid="live-date">
              {live ? formatDate(live.as_of, lang) : "–"}
            </strong>
          </p>
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
