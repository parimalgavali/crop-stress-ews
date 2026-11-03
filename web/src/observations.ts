/** Structured scouting observation records (spec 8.3), kept only in this browser —
 * same privacy model as fieldChecks (ADR 0032): nothing is sent anywhere.
 * A record captures what a person saw on a visit; it is never auto-derived from
 * thumbs up/down and never shown to retrospective annotators with future outcomes.
 */
export const OBS_SCHEMA_VERSION = 1;
export const OBS_STORAGE_KEY = "cropews.observations.v1";

export const SYMPTOMS = [
  "none_seen",
  "patchy_growth",
  "yellowing",
  "wilting",
  "standing_water",
  "bare_soil",
  "lodging",
  "other",
] as const;
export type Symptom = (typeof SYMPTOMS)[number];

export const SEVERITIES = ["mild", "moderate", "severe"] as const;
export type Severity = (typeof SEVERITIES)[number];

export const CAUSES = [
  "unknown",
  "water",
  "frost",
  "heat",
  "pest_disease",
  "nutrition",
  "mechanical",
  "not_stress",
] as const;
export type Cause = (typeof CAUSES)[number];

export const OBSERVER_TYPES = ["farmer", "agronomist", "developer", "other"] as const;
export type ObserverType = (typeof OBSERVER_TYPES)[number];

export interface Observation {
  schema_version: typeof OBS_SCHEMA_VERSION;
  field_id: string;
  /** ISO timestamp the visit happened (user-supplied), not the save time. */
  observed_at: string;
  observer_type: ObserverType;
  symptom: Symptom;
  severity: Severity | null;
  suspected_cause: Cause;
  note?: string;
  photo_ref?: string;
  review_status: "unreviewed" | "reviewed";
}

type Store = Pick<Storage, "getItem" | "setItem">;

export function loadObservations(store: Store): Observation[] {
  try {
    const v = JSON.parse(store.getItem(OBS_STORAGE_KEY) ?? "[]");
    return Array.isArray(v) ? v : [];
  } catch {
    return [];
  }
}

export function addObservation(store: Store, obs: Observation): Observation[] {
  const all = [...loadObservations(store), obs];
  try {
    store.setItem(OBS_STORAGE_KEY, JSON.stringify(all));
  } catch {
    // Private mode or full storage: the record just isn't kept.
  }
  return all;
}

/** Versioned export envelope; the schema_version lets future readers migrate. */
export function exportEnvelope(records: Observation[]) {
  return {
    schema_version: OBS_SCHEMA_VERSION,
    exported_at: new Date().toISOString(),
    records,
  };
}
