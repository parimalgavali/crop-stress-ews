import type { SeriesPoint } from "../api";
import { type Lang } from "../i18n";
import { chartSummary, LIVE_STRINGS } from "../live";

interface Props {
  series?: SeriesPoint[];
  peers?: SeriesPoint[];
  peerKind?: "cereal" | "all";
  lang: Lang;
}

const W = 300;
const H = 110;
const PAD = 8;

const day = (d: string) => Date.parse(`${d}T00:00:00Z`) / 86_400_000;

/** Field NDVI since 1 October (solid, dots) against the district peer median (dashed). */
export function SeasonChart({ series, peers, peerKind, lang }: Props) {
  const summary = chartSummary(series, peers, lang);
  if (!series || !summary) return null;
  const l = LIVE_STRINGS[lang];
  const all = [...series, ...(peers ?? [])];
  const t0 = Math.min(...all.map(([d]) => day(d)));
  const t1 = Math.max(...all.map(([d]) => day(d)), t0 + 1);
  const x = (d: string) => PAD + ((day(d) - t0) / (t1 - t0)) * (W - 2 * PAD);
  const y = (v: number) => H - PAD - Math.max(0, Math.min(1, v)) * (H - 2 * PAD);
  const path = (s: SeriesPoint[]) =>
    s.map(([d, v], i) => `${i ? "L" : "M"}${x(d).toFixed(1)},${y(v).toFixed(1)}`).join(" ");
  const peersLabel = l.chartPeers(peerKind !== "all");
  return (
    <figure className="season-chart" data-testid="season-chart">
      <figcaption>{l.chartTitle}</figcaption>
      <svg viewBox={`0 0 ${W} ${H}`} role="img" aria-label={summary}>
        {peers && peers.length > 1 && (
          <path d={path(peers)} className="peers" fill="none" />
        )}
        <path d={path(series)} className="field" fill="none" />
        {series.map(([d, v]) => (
          <circle key={d} cx={x(d)} cy={y(v)} r={3.5} className="field" />
        ))}
      </svg>
      <p className="legend" aria-hidden="true">
        <span className="key field">━●</span> {l.chartField}
        {peers && peers.length > 1 && (
          <>
            {" "}
            <span className="key peers">╌╌</span> {peersLabel}
          </>
        )}
      </p>
      <p className="hint">{summary}</p>
    </figure>
  );
}
