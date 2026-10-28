import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import type { SeriesPoint } from '../api'
import { chartSummary, compareToPeers } from '../live'
import { SeasonChart } from './SeasonChart'

const series: SeriesPoint[] = [['2026-10-05', 0.21], ['2026-10-20', 0.3], ['2026-11-02', 0.45]]
const peers: SeriesPoint[] = [['2026-10-05', 0.2], ['2026-11-01', 0.6]]

describe('season chart', () => {
  it('compares the last clear image with the latest peer median before it', () => {
    expect(compareToPeers(series, peers)).toBe('below')
    expect(compareToPeers(series, [['2026-11-01', 0.47]])).toBe('same')
    expect(compareToPeers(series, [['2026-11-03', 0.1]])).toBeNull()
    expect(compareToPeers(series, undefined)).toBeNull()
  })

  it('summarises in plain words and needs two clear images', () => {
    expect(chartSummary(series, peers, 'en')).toBe(
      'Greenness since 1 October: from 0.21 to 0.45, on 3 clear satellite images; less green than the neighbours',
    )
    expect(chartSummary(series, undefined, 'de')).toBe(
      'Pflanzengrün seit 1. Oktober: von 0,21 auf 0,45, auf 3 klaren Satellitenbildern',
    )
    expect(chartSummary(series.slice(0, 1), peers, 'en')).toBeNull()
  })

  it('renders an accessible chart with a text legend, or nothing', () => {
    const { rerender } = render(<SeasonChart series={series} peers={peers} peerKind="cereal" lang="en" />)
    expect(screen.getByRole('img')).toHaveAccessibleName(/less green than the neighbours/)
    expect(screen.getByTestId('season-chart')).toHaveTextContent('Neighbouring winter cereal fields')
    rerender(<SeasonChart series={series} peers={peers} peerKind="all" lang="en" />)
    expect(screen.getByTestId('season-chart')).toHaveTextContent('Other monitored fields nearby')
    rerender(<SeasonChart series={series.slice(0, 1)} lang="en" />)
    expect(screen.queryByTestId('season-chart')).not.toBeInTheDocument()
  })
})
