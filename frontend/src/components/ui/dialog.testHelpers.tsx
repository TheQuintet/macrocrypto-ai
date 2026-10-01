import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { useState } from 'react'
import { expect } from 'vitest'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'

type HarnessProps = {
  withDescription: boolean
  withButtons: boolean
}

/** A trigger and the dialog it opens, the way every consumer wires them. */
function DialogHarness({ withDescription, withButtons }: HarnessProps) {
  const [open, setOpen] = useState(false)

  return (
    <>
      <button type="button" onClick={() => setOpen(true)}>
        Open
      </button>
      <Dialog open={open} onOpenChange={setOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Alert settings</DialogTitle>
            {withDescription ? (
              <DialogDescription>Choose when to be notified.</DialogDescription>
            ) : null}
          </DialogHeader>
          {withButtons ? (
            <DialogFooter>
              <button type="button">First</button>
              <button type="button" onClick={() => setOpen(false)}>
                Close
              </button>
            </DialogFooter>
          ) : null}
        </DialogContent>
      </Dialog>
    </>
  )
}

export function renderDialog({
  withDescription = true,
  withButtons = true,
}: Partial<HarnessProps> = {}) {
  return render(
    <DialogHarness
      withDescription={withDescription}
      withButtons={withButtons}
    />,
  )
}

export async function openDialog() {
  await userEvent.click(screen.getByRole('button', { name: 'Open' }))
  return screen.getByRole('dialog', { name: 'Alert settings' })
}

export async function pressTab(shift = false) {
  await userEvent.keyboard(shift ? '{Shift>}{Tab}{/Shift}' : '{Tab}')
}

export async function pressEscape() {
  await userEvent.keyboard('{Escape}')
}

export async function clickOverlay() {
  await userEvent.click(screen.getByTestId('dialog-overlay'))
}

export async function clickDialogButton(name: string) {
  await userEvent.click(screen.getByRole('button', { name }))
}

export function expectFocused(name: string) {
  expect(screen.getByRole('button', { name })).toHaveFocus()
}

export function expectDialogFocused() {
  expect(screen.getByRole('dialog')).toHaveFocus()
}

export function expectDialogClosed() {
  expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
}
