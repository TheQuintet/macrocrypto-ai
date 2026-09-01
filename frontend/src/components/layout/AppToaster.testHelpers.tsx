import { render, screen } from '@testing-library/react'
import { expect } from 'vitest'
import { AppToaster } from './AppToaster'

export function renderAppToaster() {
  return render(<AppToaster />)
}

export function expectToasterCanBeDismissed() {
  expect(screen.getByTestId('app-toaster')).toHaveAttribute(
    'data-close-button',
    'true',
  )
}

export function expectToasterOverlapsUntilHover() {
  const toaster = screen.getByTestId('app-toaster')
  expect(toaster).toHaveAttribute('data-expand', 'false')
  expect(toaster).toHaveAttribute('data-visible-toasts', '8')
}
