import { cleanup, render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, beforeEach, describe, expect, it } from 'vitest'
import { CheckedIt } from './CheckedIt'

describe('CheckedIt', () => {
  beforeEach(() => localStorage.clear())
  afterEach(cleanup)

  it('saves a check on the phone, shows it, and can undo it', async () => {
    render(<CheckedIt fieldId="LWK-1" light="red" lang="en" today={() => '2026-05-04'} />)
    await userEvent.click(screen.getByRole('button', { name: /problem seen/i }))
    expect(screen.getByRole('status')).toHaveTextContent('You checked it on 4 May: problem seen')
    expect(screen.getByTestId('checked-it')).toHaveTextContent('agreed with the traffic light 1 of 1 times')
    expect(JSON.parse(localStorage.getItem('cropews.checks.v1')!)['LWK-1']).toHaveLength(1)
    await userEvent.click(screen.getByRole('button', { name: 'Undo' }))
    expect(screen.getByRole('button', { name: /looks fine/i })).toBeVisible()
  })

  it('speaks German', () => {
    render(<CheckedIt fieldId="LWK-1" light={null} lang="de" />)
    expect(screen.getByRole('button', { name: /sieht gut aus/i })).toBeVisible()
    expect(screen.getByTestId('checked-it')).toHaveTextContent('Nichts wird gesendet')
  })
})
