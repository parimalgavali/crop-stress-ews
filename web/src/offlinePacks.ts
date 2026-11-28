import type { LiveSeason } from './api';
import { speechText, STRINGS, type Lang } from './i18n';
import { evidenceSummary } from './live';
import { VISIT_TEXT } from './visitText';
import type { LocalStore, SavedField } from './savedFields';

export const PACKS_KEY = 'cropews.visit-packs.v1';
const MAX_BYTES = 4 * 1024 * 1024;
export interface PackField {
  id: string; name: string; district: string; boundary: GeoJSON.Geometry;
  warning_date: string | null; clear_image_date: string | null;
  warning: Record<Lang, string>; evidence: Record<Lang, string>;
  checklist: Record<Lang, string[]>;
}
export interface VisitPack {
  version: 1; id: string; saved_at: string; as_of: string; attribution: string;
  fields: PackField[];
}
const object = (v: unknown): v is Record<string, unknown> => !!v && typeof v === 'object' && !Array.isArray(v);
const bilingual = (v: unknown): v is Record<Lang, string> => object(v) && typeof v.en === 'string' && typeof v.de === 'string';
function validBoundary(value: unknown): boolean {
  if (!object(value)) return false;
  const polygons = value.type === 'Polygon' ? [value.coordinates] : value.type === 'MultiPolygon' ? value.coordinates : null;
  return Array.isArray(polygons) && polygons.length > 0 && polygons.every((polygon: unknown) =>
    Array.isArray(polygon) && polygon.length > 0 && polygon.every((ring: unknown) =>
      Array.isArray(ring) && ring.length >= 4 && ring.every((point: unknown) =>
        Array.isArray(point) && point.length >= 2 && point.every((n) => typeof n === 'number' && Number.isFinite(n)))));
}
function validPack(v: unknown): v is VisitPack {
  return object(v) && v.version === 1 && typeof v.id === 'string' && typeof v.saved_at === 'string' &&
    Number.isFinite(Date.parse(v.saved_at)) && typeof v.as_of === 'string' && typeof v.attribution === 'string' &&
    Array.isArray(v.fields) && v.fields.length > 0 && v.fields.every((f: unknown) => object(f) &&
      typeof f.id === 'string' && (f.warning_date === null || typeof f.warning_date === 'string') &&
      (f.clear_image_date === null || typeof f.clear_image_date === 'string') && typeof f.name === 'string' && typeof f.district === 'string' &&
      validBoundary(f.boundary) && bilingual(f.warning) && bilingual(f.evidence) &&
      object(f.checklist) && ['en', 'de'].every((lang) => Array.isArray((f.checklist as Record<string, unknown>)[lang]) &&
        ((f.checklist as Record<string, unknown>)[lang] as unknown[]).every((s) => typeof s === 'string')));
}
export function readPacks(store: LocalStore | null): VisitPack[] {
  if (!store) throw Error('Storage unavailable');
  const raw = store.getItem(PACKS_KEY) ?? '[]';
  if (raw.length > MAX_BYTES) throw Error('Pack data too large');
  const value: unknown = JSON.parse(raw);
  if (!Array.isArray(value) || !value.every(validPack)) throw Error('Unreadable packs');
  return value;
}
export function writePacks(store: LocalStore | null, packs: VisitPack[]) {
  if (!store) throw Error('Storage unavailable');
  const text = JSON.stringify(packs);
  if (packs.length > 5 || new Blob([text]).size > MAX_BYTES) throw Error('Pack limit');
  store.setItem(PACKS_KEY, text);
}
export function makePack(live: LiveSeason, ids: string[], saved: SavedField[], now = new Date()): VisitPack {
  if (!ids.length) throw Error('Choose fields');
  const fields = [...new Set(ids)].map((id): PackField => {
    const feature = live.fields.features.find((f) => f.properties.field_id === id);
    if (!feature || !validBoundary(feature.geometry)) throw Error('Field unavailable');
    const risk = live.risk?.[id];
    const warning = (lang: Lang) => risk?.horizons.length ? speechText(risk, lang) : STRINGS[lang].missingRiskNote;
    return {
      id, name: saved.find((f) => f.field_id === id)?.name || id, district: feature.properties.district,
      boundary: feature.geometry, warning_date: risk?.horizons.length ? risk.date : null,
      clear_image_date: live.evidence?.[id]?.last_clear_s2_at ?? live.conditions[id]?.s2_date ?? null,
      warning: { en: warning('en'), de: warning('de') },
      evidence: { en: evidenceSummary(live.evidence?.[id], live.conditions[id] ?? {}, 'en'), de: evidenceSummary(live.evidence?.[id], live.conditions[id] ?? {}, 'de') },
      checklist: { en: [...VISIT_TEXT.en.checklist], de: [...VISIT_TEXT.de.checklist] },
    };
  });
  // Detach the snapshot from later Live data changes.
  return JSON.parse(JSON.stringify({ version: 1, id: `${now.getTime()}-${Math.random().toString(36).slice(2)}`, saved_at: now.toISOString(), as_of: live.as_of, attribution: live.attribution, fields })) as VisitPack;
}

/** Ask the active service worker to cache only the app and its loaded JS/CSS. */
export async function prepareOfflineShell(): Promise<void> {
  if (!('serviceWorker' in navigator)) throw Error('Offline app unavailable');
  const assets = [...document.querySelectorAll<HTMLScriptElement | HTMLLinkElement>('script[src], link[rel="stylesheet"]')]
    .map((el) => el instanceof HTMLScriptElement ? el.src : el.href);
  const resources = performance.getEntriesByType('resource').map((r) => r.name)
    .filter((url) => /\/assets\/[^?]+\.(js|css)$/.test(url));
  await new Promise<void>((resolve, reject) => {
    const channel = new MessageChannel();
    let finished = false;
    const timeout = window.setTimeout(() => finish(Error('Offline preparation timed out')), 20000);
    function finish(error?: Error) {
      if (finished) return;
      finished = true;
      window.clearTimeout(timeout); channel.port1.close();
      if (error) reject(error); else resolve();
    }
    channel.port1.onmessage = (event) => finish(event.data?.ok ? undefined : Error('Offline download failed'));
    navigator.serviceWorker.ready.then((registration) => {
      if (finished) return;
      if (!registration.active) return finish(Error('Offline worker unavailable'));
      registration.active.postMessage({ type: 'PREPARE_VISITS', assets: [...new Set([...assets, ...resources])] }, [channel.port2]);
    }).catch(() => finish(Error('Offline worker unavailable')));
  });
}
