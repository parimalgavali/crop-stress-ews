import { SubfieldEntry } from "../api";
import { Lang } from "../i18n";
import { patchSummary } from "../patches";

const CELL = 9;

function cellColor(v: number | null, zone: boolean): string {
  if (zone) return "var(--warn, #b3261e)";
  if (v == null) return "transparent";
  if (v < 0.3) return "#c9b98a";
  if (v < 0.6) return "#7fae57";
  return "#2e7d32";
}

/** Pixel map of the field's freshest view with weak patches highlighted (spec 8.6). */
export function SubfieldMap({ entry, lang }: { entry: SubfieldEntry; lang: Lang }) {

  const zone = new Set(entry.grid.zone_cells.map(([r, c]) => `${r},${c}`));
  const text = patchSummary(entry, lang);
  return (
    <div className="subfield">
      <div
        role="img"
        aria-label={text}
        className="subfield-grid"
        style={{
          display: "grid",
          gridTemplateColumns: `repeat(${entry.grid.w}, ${CELL}px)`,
          gap: 1,
        }}
      >
        {entry.grid.ndvi.flatMap((row, r) =>
          row.map((v, c) => (
            <span
              key={`${r}-${c}`}
              style={{
                width: CELL,
                height: CELL,
                background: cellColor(v, zone.has(`${r},${c}`)),
              }}
            />
          )),
        )}
      </div>
      <p className="hint">
        {text}

      </p>
    </div>
  );
}
