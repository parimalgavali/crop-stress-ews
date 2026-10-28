export type Level = 'green' | 'amber' | 'red'

export interface Reason {
  code: string
  text_en: string
  text_de: string
}

export interface HorizonRisk {
  days: number
  risk: number
  level: Level
  reasons: Reason[]
}

export interface FieldRisk {
  field_id: string
  year: number
  date: string
  district: string
  horizons: HorizonRisk[]
}

export interface FieldProps {
  field_id: string
  district: string
  area_ha: number
  level: Level | null
}

export interface FieldCollection {
  type: 'FeatureCollection'
  features: { type: 'Feature'; id: string; geometry: GeoJSON.Geometry; properties: FieldProps }[]
}

// Core NRW winter-wheat districts (Soest, Warendorf, Höxter, Coesfeld, Düren, Rhein-Erft).
export const NRW_BBOX: [number, number, number, number] = [6.2, 50.6, 9.5, 52.2]
const BASE = import.meta.env.VITE_API_URL ?? '/api'
// Static GitHub Pages build (ADR 0014): read precomputed demo/<year>.json instead of the API.
export const STATIC_DEMO = import.meta.env.VITE_STATIC_DEMO === '1'

async function get<T>(path: string, params: Record<string, string | number>): Promise<T> {
  const query = new URLSearchParams(Object.entries(params).map(([k, v]) => [k, String(v)]))
  const res = await fetch(`${BASE}${path}?${query}`)
  if (!res.ok) throw new Error(`${path}: ${res.status}`)
  return res.json() as Promise<T>
}

type StaticEntry = [days: number, risk: number, level: Level, reasons: string[]]

export interface StaticSeason {
  year: number
  attribution: string
  dates: string[]
  reasons: Record<string, { en: string; de: string }>
  fields: FieldCollection
  risk: Record<string, Record<string, StaticEntry[]>>
}

const RANK: Record<Level, number> = { green: 0, amber: 1, red: 2 }
const seasons = new Map<number, Promise<StaticSeason>>()

export function loadSeason(year: number): Promise<StaticSeason> {
  let season = seasons.get(year)
  if (!season) {
    season = fetch(`${import.meta.env.BASE_URL}demo/${year}.json`).then((res) => {
      if (!res.ok) throw new Error(`demo/${year}.json: ${res.status}`)
      return res.json() as Promise<StaticSeason>
    })
    season.catch(() => seasons.delete(year))
    seasons.set(year, season)
  }
  return season
}

export function staticFields(s: StaticSeason, date: string): FieldCollection {
  const worst = (fid: string): Level | null =>
    (s.risk[fid]?.[date] ?? []).reduce<Level | null>(
      (acc, [, , lvl]) => (acc === null || RANK[lvl] > RANK[acc] ? lvl : acc),
      null,
    )
  return {
    type: 'FeatureCollection',
    features: s.fields.features.map((f) => ({
      ...f,
      properties: { ...f.properties, level: worst(f.properties.field_id) },
    })),
  }
}

export function staticRisk(s: StaticSeason, fieldId: string, date: string): FieldRisk {
  const field = s.fields.features.find((f) => f.properties.field_id === fieldId)
  const entries = s.risk[fieldId]?.[date]
  if (!field || !entries) throw new Error(`no prediction for ${fieldId} on ${date}`)
  return {
    field_id: fieldId,
    year: s.year,
    date,
    district: field.properties.district,
    horizons: entries.map(([days, risk, level, codes]) => ({
      days,
      risk,
      level,
      reasons: codes.map((code) => ({
        code,
        text_en: s.reasons[code]?.en ?? code,
        text_de: s.reasons[code]?.de ?? code,
      })),
    })),
  }
}

export const fetchDates = (year: number) =>
  STATIC_DEMO ? loadSeason(year).then((s) => s.dates) : get<string[]>('/dates', { year })

export const fetchFields = (year: number, date: string) =>
  STATIC_DEMO
    ? loadSeason(year).then((s) => staticFields(s, date))
    : get<FieldCollection>('/fields', { bbox: NRW_BBOX.join(','), year, date })

export const fetchRisk = (fieldId: string, year: number, date: string) =>
  STATIC_DEMO
    ? loadSeason(year).then((s) => staticRisk(s, fieldId, date))
    : get<FieldRisk>(`/fields/${encodeURIComponent(fieldId)}/risk`, { year, date })

// Live season (ADR 0015): current conditions for monitored parcels, refreshed every 5 days.
export interface Conditions {
  s2_date?: string
  s2_days_ago?: number
  ndvi?: number
  ndmi?: number
  ndvi_change?: number | null
  s1_date?: string
  s1_days_ago?: number
  vh_vv_db?: number
  vv_change_db?: number | null
  weather_to?: string
  rain_30d_mm?: number
  tmean_7d_c?: number
  tmin_7d_c?: number
}

export interface LiveFieldProps extends FieldProps {
  declared_crop: string
  wheat_p?: number | null
}

export interface LiveSeason {
  as_of: string
  attribution: string
  fields: { type: 'FeatureCollection'; features: { type: 'Feature'; id: string; geometry: GeoJSON.Geometry; properties: LiveFieldProps }[] }
  conditions: Record<string, Conditions>
  forecast?: Record<string, Forecast>
  risk?: Record<string, FieldRisk>
  health?: { parcels: number; with_data: number; s1_scenes_skipped: string[]; s2_scenes_skipped: string[]; minutes: number }
}

export interface Forecast {
  fc_to: string
  fc_rain_5d_mm: number
  fc_tmin_5d_c: number
  fc_frost_days: number
}

export interface ScoreHorizon {
  issued: number
  pending: number
  scored: number
  no_outcome?: number
  onsets: number
  auroc: number | null
  red_hits: number
  red_false: number
  missed: number
}

export interface Scoreboard {
  as_of: string
  horizons: Record<string, ScoreHorizon | null>
}

export async function loadScoreboard(): Promise<Scoreboard | null> {
  try {
    const res = await fetch(`${import.meta.env.BASE_URL}live/scoreboard.json`)
    return res.ok ? ((await res.json()) as Scoreboard) : null
  } catch {
    return null
  }
}

let live: Promise<LiveSeason> | null = null

export function loadLive(): Promise<LiveSeason> {
  if (!live) {
    live = fetch(`${import.meta.env.BASE_URL}live/latest.json`).then((res) => {
      if (!res.ok) throw new Error(`live/latest.json: ${res.status}`)
      return res.json() as Promise<LiveSeason>
    })
    live.catch(() => (live = null))
  }
  return live
}
