import { SubfieldEntry } from "../api";
import { Lang } from "../i18n";
import { LIVE_STRINGS } from "../live";

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
  const t = LIVE_STRINGS[lang];
  const zone = new Set(entry.grid.zone_cells.map(([r, c]) => `${r},${c}`));
  const ha = entry.zones.reduce((a, z) => a + z.area_ha, 0);
  const date = entry.date;
  const text =
    entry.zones.length > 0
      ? t.patches(entry.zones.length, Math.round(ha * 10) / 10, date)
      : t.patchesNone(date);
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
        {entry.quality.unstable ? ` — ${t.patchyView}` : ""}
      </p>
    </div>
  );
}
