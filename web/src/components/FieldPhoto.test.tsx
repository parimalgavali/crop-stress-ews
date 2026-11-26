import { act, cleanup, render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import type { Photo } from '../fieldPhoto'
import { FieldPhoto } from './FieldPhoto'

beforeEach(() => { vi.spyOn(HTMLCanvasElement.prototype, 'getContext').mockReturnValue(null) })
afterEach(() => { cleanup(); vi.restoreAllMocks() })

const ring: [number, number][] = [[8.1, 51.57], [8.104, 51.57], [8.104, 51.574], [8.1, 51.57]]

describe('FieldPhoto', () => {
  it('loads only on request and shows the dated photo with alt text', async () => {
    const load = vi.fn().mockResolvedValue({ date: '2026-10-20', width: 1, height: 1, rgba: new Uint8ClampedArray(4) })
    render(<FieldPhoto ring={ring} date="2026-10-20" dateLabel="20 October" lang="en" load={load} />)
    expect(load).not.toHaveBeenCalled()
    await userEvent.click(screen.getByRole('button', { name: /show satellite photo/i }))
    expect(load).toHaveBeenCalledWith(ring, '2026-10-20')
    expect(await screen.findByRole('img')).toHaveAccessibleName(/on 20 October, true colours/)
    expect(screen.getByTestId('field-photo')).toHaveTextContent('Copernicus Sentinel-2')
    await userEvent.click(screen.getByRole('button', { name: 'Pixels (enlarged)' }))
    expect(screen.getByRole('img')).toHaveStyle({ imageRendering: 'pixelated' })
    expect(load).toHaveBeenCalledOnce()
    await userEvent.click(screen.getByRole('button', { name: 'Overview' }))
    expect(screen.getByRole('img')).toHaveStyle({ imageRendering: 'auto' })
  })

  it('says so in plain words when there is no photo or the network fails', async () => {
    const { rerender } = render(
      <FieldPhoto ring={ring} date="2026-10-20" dateLabel="20. Oktober" lang="de" load={vi.fn().mockResolvedValue(null)} />,
    )
    await userEvent.click(screen.getByRole('button'))
    expect(await screen.findByRole('alert')).toHaveTextContent('kein Satellitenfoto gefunden')
    rerender(
      <FieldPhoto ring={ring} date="2026-10-21" dateLabel="21. Oktober" lang="de" load={vi.fn().mockRejectedValue(new Error('x'))} />,
    )
    await userEvent.click(screen.getByRole('button'))
    expect(await screen.findByRole('alert')).toHaveTextContent('konnte nicht geladen werden')
  })
})


it('does not replace the selected date with a late old photo', async () => {
  let finish: (photo: Photo) => void = () => {}
  const photo = (date: string): Photo => ({ date, width: 1, height: 1, rgba: new Uint8ClampedArray(4), pixel_size_m: 10 })
  const load = vi.fn().mockImplementationOnce(() => new Promise<Photo>((resolve) => { finish = resolve })).mockResolvedValueOnce(photo('2026-10-21'))
  const view = render(<FieldPhoto ring={ring} date="2026-10-20" dateLabel="20 October" lang="en" load={load} />)
  await userEvent.click(screen.getByRole('button'))
  view.rerender(<FieldPhoto ring={ring} date="2026-10-21" dateLabel="21 October" lang="en" load={load} />)
  await userEvent.click(screen.getByRole('button'))
  expect(await screen.findByRole('img')).toHaveAccessibleName(/21 October/)
  await act(async () => finish(photo('2026-10-20')))
  expect(screen.getByRole('img')).toHaveAccessibleName(/21 October/)
})
