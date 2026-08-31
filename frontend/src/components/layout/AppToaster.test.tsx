import { cleanup } from '@testing-library/react'
import { afterEach, describe, it, vi } from 'vitest'
import {
  expectToasterCanBeDismissed,
  expectToasterOverlapsUntilHover,
  renderAppToaster,
} from './AppToaster.testHelpers'

vi.mock('@/components/ui/sidebar', () => ({
  useSidebar: () => ({ open: true, isMobile: false }),
}))

vi.mock('@/components/ui/sonner', () => ({
  Toaster: ({
    closeButton,
    expand,
    visibleToasts,
  }: {
    closeButton?: boolean
    expand?: boolean
    visibleToasts?: number
  }) => (
    <div
      data-testid="app-toaster"
      data-close-button={closeButton ? 'true' : 'false'}
      data-expand={expand ? 'true' : 'false'}
      data-visible-toasts={visibleToasts ?? ''}
    />
  ),
}))

describe('AppToaster', () => {
  afterEach(() => {
    cleanup()
  })

  it('lets the user dismiss a toast with a close button', () => {
    renderAppToaster()
    expectToasterCanBeDismissed()
  })

  it('overlaps toasts until hover, with room for several alerts', () => {
    renderAppToaster()
    expectToasterOverlapsUntilHover()
  })
})
