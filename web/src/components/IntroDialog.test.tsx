import { cleanup, render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, expect, it, vi } from 'vitest'
import { IntroDialog } from './IntroDialog'
afterEach(cleanup)
it('focuses help, contains forward/backward tabs and supports Escape', async () => {
  const opener = document.createElement('button'); document.body.append(opener); opener.focus()
  const onClose = vi.fn()
  const view = render(<IntroDialog lang="en" onClose={onClose} />)
  const close = screen.getByRole('button', { name: 'Got it' })
  expect(close).toHaveFocus()
  await userEvent.tab(); expect(close).toHaveFocus()
  await userEvent.tab({ shift: true }); expect(close).toHaveFocus()
  await userEvent.keyboard('{Escape}'); expect(onClose).toHaveBeenCalledOnce()
  view.unmount(); expect(opener).toHaveFocus(); opener.remove()
})
