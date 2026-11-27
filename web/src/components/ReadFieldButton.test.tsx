import { act, cleanup, render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, expect, it, vi } from 'vitest'
import { ReadFieldButton } from './ReadFieldButton'
afterEach(() => { cleanup(); vi.unstubAllGlobals() })
it('uses one icon control, stops the queue and cancels on field/language changes', async () => {
  const say = vi.fn(), cancel = vi.fn()
  vi.stubGlobal('speechSynthesis', { speak: say, cancel })
  vi.stubGlobal('SpeechSynthesisUtterance', class { lang = ''; onend: (() => void) | null = null; constructor(public text: string) {} })
  const view = render(<ReadFieldButton text="First sentence. Second sentence." lang="en" identity="field-a" />)
  await userEvent.click(screen.getByRole('button', { name: /Listen/ }))
  expect(say).toHaveBeenCalledOnce()
  await userEvent.click(screen.getByRole('button', { name: /Stop/ }))
  act(() => say.mock.calls[0][0].onend?.())
  expect(say).toHaveBeenCalledOnce()
  await userEvent.click(screen.getByRole('button', { name: /Listen/ }))
  view.rerender(<ReadFieldButton text="Neues Feld." lang="de" identity="field-b" />)
  expect(screen.getByRole('button', { name: /Vorlesen/ })).toBeInTheDocument()
  expect(cancel).toHaveBeenCalled()
})
it('explains absent browser speech support and does not start playback', () => {
  vi.stubGlobal('speechSynthesis', undefined)
  render(<ReadFieldButton text="A field" lang="en" identity="a" />)
  expect(screen.getByRole('button')).toBeDisabled()
  expect(screen.getByText('Read-aloud is unavailable in this browser.')).toBeInTheDocument()
})

it('stops the previous field queue when a saved visit starts speaking', async () => {
  const say = vi.fn();
  vi.stubGlobal('speechSynthesis', { speak: say, cancel: vi.fn() });
  vi.stubGlobal('SpeechSynthesisUtterance', class { lang = ''; onend: (() => void) | null = null; constructor(public text: string) {} });
  render(<><ReadFieldButton text="Live field. More live information." lang="en" identity="live" />
    <ReadFieldButton text="Saved visit." lang="en" identity="pack" context="Saved visit" /></>);
  await userEvent.click(screen.getByRole('button', { name: 'Listen: read field summary' }));
  await userEvent.click(screen.getByRole('button', { name: 'Saved visit: Listen: read field summary' }));
  expect(screen.getByRole('button', { name: 'Listen: read field summary' })).toHaveAttribute('aria-pressed', 'false');
  act(() => say.mock.calls[0][0].onend?.());
  expect(say).toHaveBeenCalledTimes(2);
});
