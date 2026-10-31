import { useState } from "react";
import type { Level } from "../api";
import {
  addCheck,
  agreement,
  CHECK_STRINGS,
  loadChecks,
  setNote,
  undoCheck,
} from "../fieldChecks";
import { formatDate, type Lang } from "../i18n";

interface Props {
  fieldId: string;
  light: Level | null;
  lang: Lang;
  onChange?: () => void;
  store?: Storage;
  today?: () => string;
}

export function CheckedIt({
  fieldId,
  light,
  lang,
  onChange,
  store = localStorage,
  today = () => new Date().toISOString().slice(0, 10),
}: Props) {
  const t = CHECK_STRINGS[lang];
  const [all, setAll] = useState(() => loadChecks(store));
  const [noteDraft, setNoteDraft] = useState("");
  const [noteSaved, setNoteSaved] = useState(false);
  const last = all[fieldId]?.at(-1);
  const { n, agree } = agreement(all);
  const update = (next: typeof all) => {
    setAll(next);
    onChange?.();
  };

  return (
    <div className="checked-it" data-testid="checked-it">
      {last ? (
        <div role="status">
          <p>
            {t.last(formatDate(last.date, lang), last.ok)}{" "}
            <button
              type="button"
              className="link-button"
              onClick={() => update(undoCheck(store, fieldId))}
            >
              {t.undo}
            </button>
          </p>
          <p className="field-note">
            <label htmlFor="field-note">{t.noteLabel}</label>
            <textarea
              id="field-note"
              rows={2}
              maxLength={280}
              placeholder={t.noteHint}
              defaultValue={last.note ?? ""}
              onChange={(e) => {
                setNoteDraft(e.target.value);
                setNoteSaved(false);
              }}
            />
            <button
              type="button"
              className="link-button"
              disabled={noteSaved}
              onClick={() => {
                update(setNote(store, fieldId, noteDraft));
                setNoteSaved(true);
              }}
            >
              {noteSaved ? t.noteSaved : t.noteSave}
            </button>
          </p>
        </div>
      ) : (
        <>
          <p>{t.ask}</p>
          <div className="check-buttons">
            {([true, false] as const).map((ok) => (
              <button
                key={String(ok)}
                type="button"
                className="big-button"
                onClick={() =>
                  update(addCheck(store, fieldId, { date: today(), ok, light }))
                }
              >
                <span aria-hidden="true">{ok ? "👍" : "👎"}</span>{" "}
                {ok ? t.ok : t.bad}
              </button>
            ))}
          </div>
        </>
      )}
      {n > 0 && <p className="hint">{t.agree(agree, n)}</p>}
      <p className="hint">{t.private}</p>
    </div>
  );
}
