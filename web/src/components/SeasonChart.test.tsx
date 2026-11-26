import { cleanup, render, screen } from '@testing-library/react'
import { afterEach, describe, expect, it } from 'vitest'
import type { PeerSupport, SeriesPoint } from '../api'
import { chartSummary, compareToPeers } from '../live'
import { SeasonChart } from './SeasonChart'
const series: SeriesPoint[] = [['2026-10-05', 0.21], ['2026-10-20', 0.3], ['2026-11-02', 0.45]]
const peers: SeriesPoint[] = [['2026-10-05', 0.2], ['2026-11-02', 0.6]]
const support: PeerSupport = { '2026-11-02': { count: 5, previous_count: 6, retained_from_previous: 4 } }
afterEach(cleanup)
describe('season chart', () => {
  it('requires same-date, sufficient and known support', () => {
    expect(compareToPeers(series, peers, support)).toBe('below')
    expect(compareToPeers(series, [['2026-11-01', 0.47]], support)).toBeNull()
    expect(compareToPeers(series, [['2026-11-03', 0.1]], support)).toBeNull()
    expect(compareToPeers(series, peers)).toBeNull()
    expect(compareToPeers(series, peers, { '2026-11-02': { ...support['2026-11-02'], count: 4 } })).toBeNull()
  })
  it('labels mixed crops, date, count and changed coverage in the shared spoken summary', () => {
    const text = chartSummary(series, peers, 'en', { peerKind: 'all', district: 'Soest', peerSupport: support })!
    expect(text).toContain('Mixed monitored crops · Soest · 2026-11-02 · 5 contributing fields')
    expect(text).toContain('Contributing fields changed')
    expect(text).toContain('does not prove poor crop health')
    expect(chartSummary(series, peers, 'de')).toContain('Vergleich nicht verfügbar')
    expect(chartSummary(series.slice(0, 1), peers, 'en')).toBeNull()
  })
  it('renders an accessible labelled chart and observed values with unknown metadata explicit', () => {
    const { rerender } = render(<SeasonChart series={series} peers={peers} peerKind="cereal" district="Soest" peerSupport={support} lang="en" />)
    expect(screen.getByRole('img')).toHaveAccessibleName(/less green than the comparison group/)
    expect(screen.getByTestId('season-chart')).toHaveTextContent('Likely winter cereals')
    expect(screen.getByText('Observation dates and values')).toBeInTheDocument()
    expect(screen.getAllByText('2026-11-02').length).toBeGreaterThan(0)
    rerender(<SeasonChart series={series} peers={peers} peerKind="all" lang="en" />)
    expect(screen.getByTestId('season-chart')).toHaveTextContent('Mixed monitored crops')
    expect(screen.getByTestId('season-chart')).toHaveTextContent('Number of contributing fields unknown')
    rerender(<SeasonChart series={series.slice(0, 1)} lang="en" />)
    expect(screen.queryByTestId('season-chart')).not.toBeInTheDocument()
  })
})
