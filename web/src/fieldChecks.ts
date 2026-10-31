import type { Level } from "./api";
import { formatDate, type Lang } from "./i18n";

/** "I checked it" notes, kept only in this browser (ADR 0032). */
export interface FieldCheck {
  date: string;
  ok: boolean;
  /** Worst traffic light on the card when the check was saved; null outside the risk season. */
  light: Level | null;
  /** Free-text field note (US-49); only ever on this device. */
  note?: string;
}

export const STORAGE_KEY = "cropews.checks.v1";

type Store = Pick<Storage, "getItem" | "setItem">;

export function loadChecks(store: Store): Record<string, FieldCheck[]> {
  try {
    const v = JSON.parse(store.getItem(STORAGE_KEY) ?? "{}");
    return v && typeof v === "object" ? v : {};
  } catch {
    return {};
  }
}

function save(store: Store, all: Record<string, FieldCheck[]>) {
  try {
    store.setItem(STORAGE_KEY, JSON.stringify(all));
  } catch {
    // Private mode or full storage: the check just isn't kept.
  }
}

export function addCheck(store: Store, fieldId: string, check: FieldCheck) {
  const all = loadChecks(store);
  all[fieldId] = [...(all[fieldId] ?? []), check];
  save(store, all);
  return all;
}

export function undoCheck(store: Store, fieldId: string) {
  const all = loadChecks(store);
  const rest = (all[fieldId] ?? []).slice(0, -1);
  if (rest.length) all[fieldId] = rest;
  else delete all[fieldId];
  save(store, all);
  return all;
}

/** Checks made while a light was shown, and how many agreed: 👍 with green, 👎 with amber/red. */
export function agreement(all: Record<string, FieldCheck[]>): {
  n: number;
  agree: number;
} {
  const scored = Object.values(all)
    .flat()
    .filter((c) => c.light != null);
  return {
    n: scored.length,
    agree: scored.filter((c) => c.ok === (c.light === "green")).length,
  };
}

/** Attach a note to the field's latest check; empty text clears it (US-49). */
export function setNote(store: Store, fieldId: string, note: string) {
  const all = loadChecks(store);
  const last = all[fieldId]?.at(-1);
  if (!last) return all;
  const text = note.trim().slice(0, 280);
  const checks = all[fieldId].slice(0, -1);
  all[fieldId] = [...checks, { ...last, note: text || undefined }];
  save(store, all);
  return all;
}

export const CHECK_STRINGS = {
  en: {
    ask: "Been to this field? Tell your phone what you saw:",
    ok: "Looks fine",
    bad: "Problem seen",
    last: (d: string, ok: boolean) =>
      `You checked it on ${d}: ${ok ? "looks fine" : "problem seen"}`,
    undo: "Undo",
    agree: (a: number, n: number) =>
      `Your checks agreed with the traffic light ${a} of ${n} times.`,
    private: "Saved only on this phone. Nothing is sent.",
    noteLabel: "Your note about this field",
    noteHint: "e.g. waterlogged at the lower end",
    noteSave: "Save note",
    noteSaved: "Saved",
  },
  de: {
    ask: "Auf dem Feld gewesen? Sag dem Handy, was du gesehen hast:",
    ok: "Sieht gut aus",
    bad: "Problem gesehen",
    last: (d: string, ok: boolean) =>
      `Von dir geprüft am ${d}: ${ok ? "sieht gut aus" : "Problem gesehen"}`,
    undo: "Rückgängig",
    agree: (a: number, n: number) =>
      `Deine Prüfungen passten ${a} von ${n} Mal zur Ampel.`,
    private: "Nur auf diesem Handy gespeichert. Nichts wird gesendet.",
    noteLabel: "Deine Notiz zum Feld",
    noteHint: "z. B. am unteren Ende nass",
    noteSave: "Notiz speichern",
    noteSaved: "Gespeichert",
  },
};

/** Text of the last check, for the card's read-aloud. */
export function lastCheckText(
  fieldId: string,
  lang: Lang,
  store: Store = localStorage,
) {
  const last = loadChecks(store)[fieldId]?.at(-1);
  if (!last) return null;
  const base = CHECK_STRINGS[lang].last(formatDate(last.date, lang), last.ok);
  return last.note ? `${base}. ${last.note}` : base;
}
