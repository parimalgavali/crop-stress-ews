import { browserStore, unavailableStore, type LocalStore } from "../localStore";
import { CSV_TEXT, downloadVisitCsv } from "../visitCsv";
import { OBS_TEXT } from "../observationText";
import { useState } from "react";
import {
  addObservation,
  exportEnvelope,
  loadObservations,
  OBSERVER_TYPES,
  SYMPTOMS,
  SEVERITIES,
  CAUSES,
  type Observation,
  type ObserverType,
  type Symptom,
  type Severity,
  type Cause,
} from "../observations";
import { formatDate, type Lang } from "../i18n";


interface Props {
  fieldId: string;
  lang: Lang;
  store?: LocalStore;
  expanded?: boolean;
}

export function ObservationLog({ fieldId, lang, expanded = false, store = browserStore() ?? unavailableStore }: Props) {
  const t = OBS_TEXT[lang];
  const [all, setAll] = useState<Observation[]>(() => loadObservations(store));
  const [open, setOpen] = useState(false);
  const [observedAt, setObservedAt] = useState(() =>
    new Date().toISOString().slice(0, 10),
  );
  const [observer, setObserver] = useState<ObserverType>("farmer");
  const [symptom, setSymptom] = useState<Symptom>("none_seen");
  const [severity, setSeverity] = useState<Severity | "">("");
  const [cause, setCause] = useState<Cause>("unknown");
  const [note, setNote] = useState("");
  const [justSaved, setJustSaved] = useState("");
  const [csvStatus, setCsvStatus] = useState<"saved" | "error" | null>(null);
  const [failed, setFailed] = useState(false);

  const mine = all.filter((o) => o.field_id === fieldId);

  const save = () => {
    const rec: Observation = {
      schema_version: 1,
      field_id: fieldId,
      observed_at: observedAt,
      observer_type: observer,
      symptom,
      severity: severity === "" ? null : severity,
      suspected_cause: cause,
      note: note || undefined,
      review_status: "unreviewed",
    };
    setFailed(false);
    setJustSaved("");
    try {
      setAll(addObservation(store, rec));
    } catch {
      setFailed(true);
      return;
    }
    setJustSaved(observedAt);
    setNote("");
    setOpen(false);
  };

  const download = () => {
    const blob = new Blob([JSON.stringify(exportEnvelope(all), null, 1)], {
      type: "application/json",
    });
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = "field-observations.json";
    a.click();
    URL.revokeObjectURL(a.href);
  };

  return (
    <details className="evidence" open={expanded || undefined}>
      <summary>{t.title}</summary>
      {mine.length === 0 ? (
        <p className="hint">{t.none}</p>
      ) : (
        <ul>
          {mine.map((o, i) => (
            <li key={i}>
              {formatDate(o.observed_at, lang)} · {t.labels[o.observer_type]} ·{" "}
              {t.labels[o.symptom]}
              {o.severity ? ` (${t.labels[o.severity]})` : ""} ·{" "}
              {t.labels[o.suspected_cause]}
              {o.note ? ` — ${o.note}` : ""}
            </li>
          ))}
        </ul>
      )}
      {failed && <p role="alert">{t.error}</p>}
      {justSaved && <p role="status">{t.saved(formatDate(justSaved, lang))}</p>}
      {!open ? (
        <button type="button" className="big-button" onClick={() => setOpen(true)}>
          {t.add}
        </button>
      ) : (
        <form className="obs-form" onSubmit={(e) => { e.preventDefault(); save(); }}>
          <label>
            {t.when}{" "}
            <input
              type="date"
              required
              value={observedAt}
              onChange={(e) => setObservedAt(e.target.value)}
            />
          </label>
          <label>
            {t.who}{" "}
            <select
              value={observer}
              onChange={(e) => setObserver(e.target.value as ObserverType)}
            >
              {OBSERVER_TYPES.map((o) => (
                <option key={o} value={o}>
                  {t.labels[o]}
                </option>
              ))}
            </select>
          </label>
          <label>
            {t.symptom}{" "}
            <select
              value={symptom}
              onChange={(e) => setSymptom(e.target.value as Symptom)}
            >
              {SYMPTOMS.map((x) => (
                <option key={x} value={x}>
                  {t.labels[x]}
                </option>
              ))}
            </select>
          </label>
          <label>
            {t.severity}{" "}
            <select
              value={severity}
              onChange={(e) => setSeverity(e.target.value as Severity | "")}
            >
              <option value="">{t.unknown}</option>
              {SEVERITIES.map((x) => (
                <option key={x} value={x}>
                  {t.labels[x]}
                </option>
              ))}
            </select>
          </label>
          <label>
            {t.cause}{" "}
            <select
              value={cause}
              onChange={(e) => setCause(e.target.value as Cause)}
            >
              {CAUSES.map((x) => (
                <option key={x} value={x}>
                  {t.labels[x]}
                </option>
              ))}
            </select>
          </label>
          <label>
            {t.note}{" "}
            <input
              type="text"
              value={note}
              onChange={(e) => setNote(e.target.value)}
            />
          </label>
          <button type="submit" className="big-button">
            {t.save}
          </button>
        </form>
      )}
      {all.length > 0 && (
        <button type="button" className="big-button" onClick={download}>
          {t.export}
        </button>
      )}
      {all.length > 0 && <>
        <button type="button" className="big-button" onClick={() => {
          try { downloadVisitCsv(store, lang); setCsvStatus("saved"); } catch { setCsvStatus("error"); }
        }}>{CSV_TEXT[lang].export}</button>
        <p className="hint">{CSV_TEXT[lang].hint}</p>
      </>}
      {csvStatus && <p role={csvStatus === "error" ? "alert" : "status"}>{CSV_TEXT[lang][csvStatus]}</p>}
      <p className="hint">{t.privacy}</p>
    </details>
  );
}
