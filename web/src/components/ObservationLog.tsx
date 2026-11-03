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

const T = {
  en: {
    title: "📝 Field visit record",
    add: "Record what you saw",
    when: "When were you there?",
    who: "Who visited?",
    symptom: "What did you see?",
    severity: "How bad?",
    cause: "Suspected cause",
    note: "Note (optional)",
    save: "Save record",
    saved: (d: string) => `Saved: visit on ${d}`,
    none: "No visit records on this device yet.",
    export: "Export all records (JSON)",
    unknown: "not sure",
    privacy: "Records stay on this device. Nothing is sent.",
    labels: {
      none_seen: "nothing wrong seen",
      patchy_growth: "patchy growth",
      yellowing: "yellowing",
      wilting: "wilting",
      standing_water: "standing water",
      bare_soil: "bare soil",
      lodging: "lodging / flattened",
      other: "other",
      mild: "mild",
      moderate: "moderate",
      severe: "severe",
      water: "water (too much / too little)",
      frost: "frost",
      heat: "heat",
      pest_disease: "pest or disease",
      nutrition: "nutrition",
      mechanical: "machinery / other damage",
      not_stress: "not crop stress",
      farmer: "farmer",
      agronomist: "agronomist",
      developer: "developer",
    } as Record<string, string>,
  },
  de: {
    title: "📝 Feld-Besuchsprotokoll",
    add: "Festhalten, was Sie gesehen haben",
    when: "Wann waren Sie dort?",
    who: "Wer war vor Ort?",
    symptom: "Was haben Sie gesehen?",
    severity: "Wie schlimm?",
    cause: "Vermutete Ursache",
    note: "Notiz (optional)",
    save: "Eintrag speichern",
    saved: (d: string) => `Gespeichert: Besuch am ${d}`,
    none: "Noch keine Besuchseinträge auf diesem Gerät.",
    export: "Alle Einträge exportieren (JSON)",
    unknown: "unsicher",
    privacy: "Einträge bleiben auf diesem Gerät. Es wird nichts gesendet.",
    labels: {
      none_seen: "nichts Auffälliges gesehen",
      patchy_growth: "unterschiedlicher Bewuchs",
      yellowing: "Vergilbung",
      wilting: "Welken",
      standing_water: "stehendes Wasser",
      bare_soil: "offener Boden",
      lodging: "Lagerung / umgelegt",
      other: "sonstiges",
      mild: "leicht",
      moderate: "mittel",
      severe: "schwer",
      water: "Wasser (zu viel / zu wenig)",
      frost: "Frost",
      heat: "Hitze",
      pest_disease: "Schädling oder Krankheit",
      nutrition: "Nährstoffe",
      mechanical: "Maschinen- / sonstiger Schaden",
      not_stress: "kein Pflanzenstress",
      farmer: "Landwirt/in",
      agronomist: "Agronom/in",
      developer: "Entwickler/in",
    } as Record<string, string>,
  },
};

interface Props {
  fieldId: string;
  lang: Lang;
  store?: Storage;
}

export function ObservationLog({ fieldId, lang, store = localStorage }: Props) {
  const t = T[lang];
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
    setAll(addObservation(store, rec));
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
    <details className="evidence">
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
      {justSaved && <p role="status">{t.saved(formatDate(justSaved, lang))}</p>}
      {!open ? (
        <button type="button" className="big-button" onClick={() => setOpen(true)}>
          {t.add}
        </button>
      ) : (
        <div className="obs-form">
          <label>
            {t.when}{" "}
            <input
              type="date"
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
          <button type="button" className="big-button" onClick={save}>
            {t.save}
          </button>
        </div>
      )}
      {all.length > 0 && (
        <button type="button" className="big-button" onClick={download}>
          {t.export}
        </button>
      )}
      <p className="hint">{t.privacy}</p>
    </details>
  );
}
