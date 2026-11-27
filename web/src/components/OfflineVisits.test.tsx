import { cleanup, render, screen, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { afterEach, expect, it, vi } from 'vitest';
import { OfflineVisits } from './OfflineVisits';
import { makePack, PACKS_KEY, readPacks, writePacks } from '../offlinePacks';
import type { LiveSeason } from '../api';
const live: LiveSeason = {
  as_of: '2026-11-26', attribution: 'Boundary source: test', conditions: {},
  fields: { type: 'FeatureCollection', features: [{ type: 'Feature', id: 'LWK-1', geometry: { type: 'Polygon', coordinates: [[[8, 51], [8.01, 51], [8.01, 51.01], [8, 51]]] }, properties: { field_id: 'LWK-1', district: 'Soest', area_ha: 4, level: null, declared_crop: 'unknown' } }] },
};
const memory = () => {
  const values = new Map<string, string>();
  return { getItem: (k: string) => values.get(k) ?? null, setItem: (k: string, v: string) => { values.set(k, v); } };
};
afterEach(cleanup);
it('freezes both languages and boundaries independently of later live updates', () => {
  const source = structuredClone(live);
  const pack = makePack(source, ['LWK-1', 'LWK-1'], [{ field_id: 'LWK-1', name: 'Gate field', district: 'Soest' }]);
  source.fields.features[0].properties.district = 'changed';
  expect(pack.fields).toHaveLength(1);
  expect(pack.fields[0]).toMatchObject({ name: 'Gate field', district: 'Soest', warning_date: null, clear_image_date: null });
  expect(pack.fields[0].warning.en).toContain('does not mean low risk');
  expect(pack.fields[0].warning.de).toContain('nicht geringes Risiko');
  const store = memory(); writePacks(store, [pack]);
  expect(readPacks(store)).toEqual([pack]);
  store.setItem(PACKS_KEY, '[{"version":1}]');
  expect(() => readPacks(store)).toThrow();
});
it('does not save a pack when the app download fails', async () => {
  const store = memory(); const prepare = vi.fn().mockRejectedValue(Error('Offline'));
  render(<OfflineVisits live={live} lang="en" store={store} prepare={prepare} />);
  await userEvent.click(screen.getByText('Choose fields for an offline pack', { selector: 'summary' }));
  await userEvent.click(screen.getByRole('checkbox'));
  await userEvent.click(screen.getByRole('button', { name: 'Save selected visits' }));
  expect(screen.getByRole('alert')).toHaveTextContent('App download failed');
  expect(readPacks(store)).toEqual([]);
});
it('retains existing packs on storage failure and leaves unreadable data untouched', async () => {
  const data = memory(); writePacks(data, [makePack(live, ['LWK-1'], [])]);
  const original = data.getItem(PACKS_KEY);
  const store = { ...data, setItem: () => { throw Error('Quota'); } };
  render(<OfflineVisits live={live} lang="en" store={store} prepare={async () => {}} />);
  await userEvent.click(screen.getByText('Choose fields for an offline pack', { selector: 'summary' }));
  await userEvent.click(screen.getByRole('checkbox'));
  await userEvent.click(screen.getByRole('button', { name: 'Save selected visits' }));
  expect(screen.getByRole('alert')).toHaveTextContent('Could not save the pack');
  expect(data.getItem(PACKS_KEY)).toBe(original);
  cleanup(); data.setItem(PACKS_KEY, 'broken');
  render(<OfflineVisits live={live} lang="en" store={data} />);
  expect(screen.getByRole('alert')).toHaveTextContent('Nothing has been overwritten');
  expect(screen.getByRole('button', { name: 'Save selected visits' })).toBeDisabled();
  expect(data.getItem(PACKS_KEY)).toBe('broken');
});
it.each(['en', 'de'] as const)('opens saved data without live data, records a visit and removes only the pack (%s)', async (lang) => {
  const store = memory(); writePacks(store, [makePack(live, ['LWK-1'], [])]);
  render(<OfflineVisits live={null} lang={lang} store={store} />);
  await userEvent.click(screen.getByRole('button', { name: lang === 'en' ? 'Open saved pack' : 'Gespeichertes Paket öffnen' }));
  const visit = screen.getByRole('region', { name: /LWK-1/ });
  expect(within(visit).getByText(lang === 'en' ? /No forecast is available/ : /Keine Vorhersage verfügbar/)).toBeVisible();
  expect(within(visit).getByRole('button', { name: lang === 'en' ? 'Record what you saw' : 'Festhalten, was Sie gesehen haben' })).toBeVisible();
  await userEvent.click(within(visit).getByText(lang === 'en' ? 'Saved field boundary (outline only; no street map)' : 'Gespeicherte Feldgrenze (nur Umriss; keine Straßenkarte)'));
  expect(within(visit).getByRole('img')).toBeVisible();
  const records = '[{"field_id":"LWK-1"}]'; store.setItem('cropews.observations.v1', records);
  await userEvent.click(screen.getByRole('button', { name: lang === 'en' ? 'Remove this pack' : 'Dieses Paket entfernen' }));
  expect(readPacks(store)).toEqual([]);
  expect(store.getItem('cropews.observations.v1')).toBe(records);
});
