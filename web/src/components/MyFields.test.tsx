import { cleanup, render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, expect, it, vi } from 'vitest'
import { MyFields } from './MyFields'
import { loadSavedFields, SAVED_FIELDS_KEY } from '../savedFields'
import type { LiveSeason } from '../api'
afterEach(() => { cleanup(); localStorage.clear() })
const live = { fields: { features: [{ properties: { field_id: 'a', district: 'Soest' } }] }, risk: {} } as unknown as LiveSeason
it('saves, renames, reopens and removes a field without changing its id', async () => {
  const open = vi.fn()
  const props = { live, selected: 'a', onSelect: open, lang: 'en' as const, store: localStorage }
  const view = render(<MyFields {...props} />)
  await userEvent.type(screen.getByLabelText('Name for this field'), 'Behind the barn')
  await userEvent.click(screen.getByRole('button', { name: 'Save field name' }))
  expect(loadSavedFields(localStorage)[0].field_id).toBe('a')
  view.unmount(); render(<MyFields {...props} />)
  expect(screen.getByText(/No forecast available/)).toBeInTheDocument()
  await userEvent.click(screen.getByRole('button', { name: 'Behind the barn' }))
  expect(open).toHaveBeenCalledWith('a')
  await userEvent.clear(screen.getByLabelText('Name for this field'))
  await userEvent.type(screen.getByLabelText('Name for this field'), 'North')
  await userEvent.click(screen.getByRole('button', { name: 'Save field name' }))
  expect(loadSavedFields(localStorage)).toHaveLength(1)
  expect(loadSavedFields(localStorage)[0].name).toBe('North')
  await userEvent.click(screen.getByRole('button', { name: 'Remove: North' }))
  expect(loadSavedFields(localStorage)).toEqual([])
})
it('reports storage failure without claiming the field was saved', async () => {
  render(<MyFields live={live} selected="a" onSelect={vi.fn()} lang="de" store={{ getItem: () => null, setItem: () => { throw Error('full') } }} />)
  await userEvent.click(screen.getByRole('button', { name: 'Feldname speichern' }))
  expect(screen.getByRole('alert')).toHaveTextContent('Speichern fehlgeschlagen')
  expect(screen.queryByRole('status')).not.toBeInTheDocument()
})
it('keeps missing fields visible and tolerates invalid stored data', () => {
  localStorage.setItem(SAVED_FIELDS_KEY, JSON.stringify([{ field_id: 'old', name: 'Old', district: 'Soest' }]))
  render(<MyFields live={live} selected={null} onSelect={vi.fn()} lang="en" store={localStorage} />)
  expect(screen.getByRole('button', { name: 'Old' })).toBeDisabled()
  expect(screen.getByText(/Not currently monitored/)).toBeInTheDocument()
  localStorage.setItem(SAVED_FIELDS_KEY, '{')
  expect(loadSavedFields(localStorage)).toEqual([])
})
