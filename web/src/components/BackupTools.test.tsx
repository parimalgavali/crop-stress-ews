import { cleanup, render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, expect, it, vi } from 'vitest'
import { BackupTools } from './BackupTools'
afterEach(cleanup)
it('downloads only when asked and describes privacy and exclusions', async () => {
  const download = vi.fn()
  render(<BackupTools lang="en" store={localStorage} download={download} />)
  expect(download).not.toHaveBeenCalled()
  expect(screen.getByText(/Photo files/)).toBeInTheDocument()
  await userEvent.click(screen.getByRole('button', { name: 'Download my backup' }))
  expect(download).toHaveBeenCalledOnce()
  expect(screen.getByRole('status')).toHaveTextContent('download started')
})
it('reports failures in German', async () => {
  render(<BackupTools lang="de" store={null} />)
  await userEvent.click(screen.getByRole('button', { name: 'Meine Sicherung herunterladen' }))
  expect(screen.getByRole('alert')).toHaveTextContent('Sicherung fehlgeschlagen')
})
