import { act, cleanup, render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { LiveCard } from './LiveCard'

afterEach(() => { cleanup(); vi.unstubAllGlobals() })

describe('Live evidence summary', () => {
  it('shows limited evidence and image freshness outside collapsed details', () => {
    render(<LiveCard cond={{}} crop="" district="Soest" lang="en" evidence={{
      field_id: 'a', quality_status: 'limited', last_clear_s2_at: '2027-04-01', s2_days_ago: 12,
    }} />)
    const summary = screen.getByTestId('evidence-summary')
    expect(summary).toBeVisible()
    expect(summary.closest('details')).toBeNull()
    expect(summary).toHaveTextContent('Evidence: limited')
    expect(summary).toHaveTextContent('12 days ago')
    expect(summary).toHaveTextContent('Low risk does not confirm')
  })
  it('keeps absent quality unknown even with a recent image', () => {
    render(<LiveCard cond={{ s2_date: '2027-04-10', s2_days_ago: 0 }} crop="" district="Soest" lang="en" />)
    expect(screen.getByTestId('evidence-summary')).toHaveTextContent('Evidence: unknown')
    expect(screen.getByTestId('evidence-summary')).toHaveTextContent('0 days ago')
  })
  it('shows missing evidence in German and reads the summary aloud', async () => {
    const speak = vi.fn()
    vi.stubGlobal('speechSynthesis', { speak, cancel: vi.fn() })
    vi.stubGlobal('SpeechSynthesisUtterance', class {
      lang = ''; onend: (() => void) | null = null
      constructor(public text: string) {}
    })
    render(<LiveCard cond={{}} crop="" district="Soest" lang="de" />)
    const summary = screen.getByTestId('evidence-summary')
    expect(summary).toHaveTextContent('Datenlage: unbekannt')
    expect(summary).toHaveTextContent('noch keins')
    await userEvent.click(screen.getByRole('button', { name: /Vorlesen/ }))
    act(() => {
      for (let i = 0; i < speak.mock.calls.length; i++) speak.mock.calls[i][0].onend?.()
    })
    const spoken = speak.mock.calls.map((c) => c[0].text).join(' ')
    expect(spoken).toContain('Datenlage: unbekannt')
    expect(spoken).toContain('Klares Satellitenbild: noch keins')
  })
})
