import { useState } from 'react';
import type { LiveSeason } from '../api';
import type { Lang } from '../i18n';
import { browserStore, loadSavedFields, type LocalStore } from '../savedFields';
import { makePack, prepareOfflineShell, readPacks, writePacks, type PackField, type VisitPack } from '../offlinePacks';
import { PACK_TEXT } from '../offlineText';
import { VISIT_TEXT } from '../visitText';
import { ReadFieldButton } from './ReadFieldButton';
import { ObservationLog } from './ObservationLog';

/** Deliberately no basemap or remote image requests in a saved visit. */
function Boundary({ geometry, label }: { geometry: GeoJSON.Geometry; label: string }) {
  const polygons = geometry.type === 'Polygon' ? [geometry.coordinates] : geometry.type === 'MultiPolygon' ? geometry.coordinates : [];
  const points = polygons.flat(2);
  if (!points.length || points.some((p) => p.length < 2 || !Number.isFinite(p[0]) || !Number.isFinite(p[1]))) return null;
  const xs = points.map((p) => p[0]), ys = points.map((p) => p[1]);
  const x0 = xs.reduce((a, b) => Math.min(a, b), Infinity), y0 = ys.reduce((a, b) => Math.min(a, b), Infinity);
  const xmax = xs.reduce((a, b) => Math.max(a, b), -Infinity), ymax = ys.reduce((a, b) => Math.max(a, b), -Infinity);
  const aspect = Math.cos((y0 + ymax) * Math.PI / 360);
  const scale = Math.max((xmax - x0) * aspect, ymax - y0);
  if (!scale) return null;
  const path = polygons.map((polygon) => polygon.map((ring) => ring.map(([x, y], i) => `${i ? 'L' : 'M'}${10 + (x - x0) * aspect / scale * 180},${190 - (y - y0) / scale * 180}`).join(' ') + ' Z').join(' '));
  return <svg viewBox="0 0 200 200" role="img" aria-label={label} className="pack-boundary">
    {path.map((d, i) => <path key={i} d={d} fill="#e8f2e8" stroke="#166020" strokeWidth="2" fillRule="evenodd" />)}
  </svg>;
}
function SavedVisit({ pack, field, lang }: { pack: VisitPack; field: PackField; lang: Lang }) {
  const t = PACK_TEXT[lang], v = VISIT_TEXT[lang];
  const text = [field.name, field.id, field.district, t.savedAt, pack.saved_at, t.asOf, pack.as_of,
    t.snapshot, field.warning_date ? `${t.warningDate} ${field.warning_date}` : t.noWarningDate, field.clear_image_date ? `${t.imageDate} ${field.clear_image_date}` : t.noImage, field.warning[lang], field.evidence[lang], ...field.checklist[lang], v.limits, t.limits].join('. ');
  return <section className="card saved-visit" aria-label={`${v.title}: ${field.name}`}>
    <h3>{field.name} · {field.id}</h3>
    <p>{field.district}</p>
    <p>{t.savedAt} {pack.saved_at}</p><p>{t.asOf} {pack.as_of}</p>
    <p className="hint">{t.snapshot}</p>
    <ReadFieldButton text={text} lang={lang} context={t.readSaved} identity={`${pack.id}-${field.id}`} />
    <p>{field.warning_date ? `${t.warningDate} ${field.warning_date}` : t.noWarningDate}</p>
    <p>{field.warning[lang]}</p>
    <p>{field.clear_image_date ? `${t.imageDate} ${field.clear_image_date}` : t.noImage}</p>
    <p>{field.evidence[lang]}</p>
    <h4>{v.checkTitle}</h4><ul>{field.checklist[lang].map((s) => <li key={s}>{s}</li>)}</ul>
    <p className="hint">{v.limits}</p>
    <ObservationLog fieldId={field.id} lang={lang} expanded />
    <details className="evidence"><summary>{t.boundary}</summary><Boundary geometry={field.boundary} label={t.boundary} /><p className="hint">{pack.attribution}</p></details>
    <p className="hint">{t.limits}</p>
  </section>;
}
export function OfflineVisits({ live, lang, store = browserStore(), prepare = prepareOfflineShell }: {
  live: LiveSeason | null; lang: Lang; store?: LocalStore | null; prepare?: () => Promise<void>;
}) {
  const t = PACK_TEXT[lang];
  const [initial] = useState(() => { try { return { packs: readPacks(store), error: false }; } catch { return { packs: [], error: true }; } });
  const [packs, setPacks] = useState<VisitPack[]>(initial.packs);
  const [chosen, setChosen] = useState<string[]>([]);
  const [status, setStatus] = useState<keyof Pick<typeof t, 'preparing' | 'downloading' | 'failedDownload' | 'failedStorage' | 'saved' | 'removed' | 'removeError'> | null>(null);
  const [opened, setOpened] = useState<string | null>(null);
  const [fieldId, setFieldId] = useState('');
  const busy = status === 'preparing' || status === 'downloading';
  const pack = packs.find((p) => p.id === opened);
  const field = pack?.fields.find((f) => f.id === fieldId) ?? pack?.fields[0];
  const names = loadSavedFields(store);
  const save = async () => {
    if (!live || !chosen.length || busy) return;
    let snapshot: VisitPack;
    try { snapshot = makePack(live, chosen, names); } catch { setStatus('failedStorage'); return; }
    setStatus('preparing');
    try { await prepare(); } catch { setStatus('failedDownload'); return; }
    setStatus('downloading');
    try {
      const next = [...readPacks(store), snapshot];
      writePacks(store, next); setPacks(next); setStatus('saved');
    } catch { setStatus('failedStorage'); }
  };
  return <section className="offline-visits" aria-label={t.title}>
    <h2>{t.title}</h2><p className="hint">{t.snapshot}</p>
    {initial.error && <p role="alert">{t.unreadable}</p>}
    {live && <>
      <p className="hint">{t.selectHint}</p>
      <details className="evidence"><summary>{t.choose}</summary>
        <fieldset disabled={busy || initial.error} className="pack-choices"><legend>{t.choose}</legend>
          {live.fields.features.map((f) => <label key={f.properties.field_id}>
            <input type="checkbox" checked={chosen.includes(f.properties.field_id)} onChange={(e) => setChosen((before) => e.target.checked ? [...before, f.properties.field_id] : before.filter((id) => id !== f.properties.field_id))} />
            {names.find((n) => n.field_id === f.properties.field_id)?.name ?? f.properties.field_id} · {f.properties.field_id} · {f.properties.district}
          </label>)}
        </fieldset>
      </details>
      <button type="button" disabled={busy || initial.error || !chosen.length} onClick={save}>{t.save}</button>
    </>}
    {status && <p role={status.startsWith('failed') || status === 'removeError' ? 'alert' : 'status'}>{t[status]}</p>}
    {!packs.length && <p>{t.empty}</p>}
    {packs.map((p) => <div className="pack-item" key={p.id}>
      <p>{t.savedAt} {p.saved_at} · {t.asOf} {p.as_of}</p>
      <ul>{p.fields.map((f) => <li key={f.id}>{f.name} · {f.id} — {t.ready}</li>)}</ul>
      <button type="button" onClick={() => { setOpened(p.id); setFieldId(p.fields[0].id); }}>{t.open}</button>
      <button type="button" disabled={busy} onClick={() => {
        try {
          const next = readPacks(store).filter((item) => item.id !== p.id);
          writePacks(store, next); setPacks(next); if (opened === p.id) setOpened(null); setStatus('removed');
        } catch { setStatus('removeError'); }
      }}>{t.remove}</button>
    </div>)}
    {pack && field && <>
      <button type="button" onClick={() => setOpened(null)}>{t.back}</button>
      <label>{t.field}<select value={field.id} onChange={(e) => setFieldId(e.target.value)}>{pack.fields.map((f) => <option value={f.id} key={f.id}>{f.name} · {f.id}</option>)}</select></label>
      <SavedVisit key={`${pack.id}-${field.id}`} pack={pack} field={field} lang={lang} />
    </>}
    <p className="hint">{t.limits}</p>
  </section>;
}
