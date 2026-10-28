import { useEffect, useRef } from 'react'
import maplibregl from 'maplibre-gl'
import 'maplibre-gl/dist/maplibre-gl.css'
import type { FieldCollection } from '../api'

const COLORS = ['match', ['get', 'level'], 'red', '#d7191c', 'amber', '#fdae61', 'green', '#1a9641', '#9e9e9e']

const STYLE: maplibregl.StyleSpecification = {
  version: 8,
  sources: {
    osm: {
      type: 'raster',
      tiles: ['https://tile.openstreetmap.org/{z}/{x}/{y}.png'],
      tileSize: 256,
      attribution: '© OpenStreetMap contributors',
    },
  },
  layers: [{ id: 'osm', type: 'raster', source: 'osm' }],
}

function bounds(features: FieldCollection['features']): maplibregl.LngLatBounds {
  const b = new maplibregl.LngLatBounds()
  for (const { geometry: g } of features) {
    const rings = g.type === 'Polygon' ? g.coordinates : g.type === 'MultiPolygon' ? g.coordinates.flat() : []
    for (const ring of rings) for (const p of ring) b.extend(p as [number, number])
  }
  return b
}

interface Props {
  fields: FieldCollection | null
  selected: string | null
  onSelect: (fieldId: string) => void
}

export function MapView({ fields, selected, onSelect }: Props) {
  const container = useRef<HTMLDivElement>(null)
  const map = useRef<maplibregl.Map | null>(null)
  const fitted = useRef(false)
  const onSelectRef = useRef(onSelect)
  onSelectRef.current = onSelect

  useEffect(() => {
    if (!container.current) return
    const m = new maplibregl.Map({
      container: container.current,
      style: STYLE,
      center: [7.9, 51.6],
      zoom: 8,
    })
    m.on('load', () => {
      m.addSource('fields', { type: 'geojson', data: { type: 'FeatureCollection', features: [] } })
      m.addLayer({
        id: 'fields-fill',
        type: 'fill',
        source: 'fields',
        paint: { 'fill-color': COLORS as never, 'fill-opacity': 0.75 },
      })
      m.addLayer({
        id: 'fields-line',
        type: 'line',
        source: 'fields',
        paint: { 'line-color': '#000', 'line-width': ['case', ['==', ['id'], ''], 4, 1] },
      })
      m.on('click', 'fields-fill', (e) => {
        const id = e.features?.[0]?.properties?.field_id
        if (typeof id === 'string') onSelectRef.current(id)
      })
      m.on('mouseenter', 'fields-fill', () => (m.getCanvas().style.cursor = 'pointer'))
      m.on('mouseleave', 'fields-fill', () => (m.getCanvas().style.cursor = ''))
      map.current = m
      m.fire('fields-ready')
    })
    return () => {
      m.remove()
      map.current = null
    }
  }, [])

  useEffect(() => {
    const update = () => {
      const m = map.current
      const src = m?.getSource('fields') as maplibregl.GeoJSONSource | undefined
      if (!m || !src || !fields) return
      src.setData(fields as GeoJSON.FeatureCollection)
      if (!fitted.current && fields.features.length > 0) {
        m.fitBounds(bounds(fields.features), { padding: 40, duration: 0 })
        fitted.current = true
      }
    }
    if (map.current) update()
    else {
      const t = setInterval(() => map.current && (update(), clearInterval(t)), 200)
      return () => clearInterval(t)
    }
  }, [fields])

  useEffect(() => {
    const f = fields?.features.find((x) => x.properties.field_id === selected)
    if (map.current && f) map.current.fitBounds(bounds([f]), { padding: 80, maxZoom: 14 })
  }, [selected, fields])

  useEffect(() => {
    map.current?.setPaintProperty('fields-line', 'line-width', [
      'case',
      ['==', ['get', 'field_id'], selected ?? ''],
      4,
      1,
    ])
  }, [selected])

  return <div ref={container} className="map" role="img" aria-label="Map of wheat fields coloured by risk" />
}
