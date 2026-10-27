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

async function get<T>(path: string, params: Record<string, string | number>): Promise<T> {
  const query = new URLSearchParams(Object.entries(params).map(([k, v]) => [k, String(v)]))
  const res = await fetch(`${BASE}${path}?${query}`)
  if (!res.ok) throw new Error(`${path}: ${res.status}`)
  return res.json() as Promise<T>
}

export const fetchDates = (year: number) => get<string[]>('/dates', { year })

export const fetchFields = (year: number, date: string) =>
  get<FieldCollection>('/fields', { bbox: NRW_BBOX.join(','), year, date })

export const fetchRisk = (fieldId: string, year: number, date: string) =>
  get<FieldRisk>(`/fields/${encodeURIComponent(fieldId)}/risk`, { year, date })
