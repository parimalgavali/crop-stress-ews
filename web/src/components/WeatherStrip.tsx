import type { Forecast } from "../api";
import { LIVE_STRINGS } from "../live";
import type { Lang } from "../i18n";

/** Rain bars + low/high temperatures for the field's 5-day ICON forecast (US-45). */
export default function WeatherStrip({
  days,
  lang,
}: {
  days: NonNullable<Forecast["fc_days"]>;
  lang: Lang;
}) {
  const l = LIVE_STRINGS[lang];
  const locale = lang === "de" ? "de-DE" : "en-GB";
  const maxRain = Math.max(5, ...days.map((d) => d.pr));
  const label = `${l.weatherLabel}: ${days
    .map((d) => {
      const wd = new Date(`${d.date}T00:00:00`).toLocaleDateString(locale, {
        weekday: "short",
      });
      return `${wd} ${Math.round(d.tmin)}°/${Math.round(d.tmax)}°, ${d.pr} mm`;
    })
    .join("; ")}`;
  return (
    <div className="fcstrip" role="img" aria-label={label}>
      {days.map((d) => (
        <div className="fcday" key={d.date} aria-hidden="true">
          <span>
            {new Date(`${d.date}T00:00:00`).toLocaleDateString(locale, {
              weekday: "short",
            })}
          </span>
          <span className="fcbar">
            <i style={{ height: `${Math.max(2, (d.pr / maxRain) * 100)}%` }} />
          </span>
          <span className="fct">
            {Math.round(d.tmin)}°/{Math.round(d.tmax)}°
          </span>
        </div>
      ))}
    </div>
  );
}
