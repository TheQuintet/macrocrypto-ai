import { screen } from '@testing-library/react'
import type { UserEvent } from '@testing-library/user-event'
import { expect, vi } from 'vitest'
import { AlertManagement } from './AlertManagement'
import { usePriceAlerts } from '@/hooks/alerts/usePriceAlerts'
import { useBtcPriceSnapshotQuery } from '@/hooks/useBtcPriceSnapshotQuery'
import { macroAlertApi } from '@/api/alerts/macroAlerts'
import { macroEvents } from './macro/MacroAlertForm.testHelpers'
import { mockAlert } from './price/__tests__/testHelpers'
import type { PriceAlert } from '@/types/alerts/priceAlert'
import type { BtcPriceSnapshot } from '@/types/btcPrice'
import { renderWithQuery } from '@/test/renderWithQuery'

const defaultUserId = 'b5e2102c-c4ac-46f9-95c3-2a3c389399a9'

type ManagementOptions = {
  alerts?: PriceAlert[]
}

export function renderAlertManagement(overrides: ManagementOptions = {}) {
  vi.mocked(usePriceAlerts).mockReturnValue({
    // A non-empty list keeps the empty state's own "New alert" button out of the way.
    alerts: overrides.alerts ?? [mockAlert],
    isLoading: false,
    error: null,
    fetch: vi.fn(),
    create: vi.fn().mockResolvedValue(undefined),
    update: vi.fn().mockResolvedValue(undefined),
    remove: vi.fn().mockResolvedValue(undefined),
  } as unknown as ReturnType<typeof usePriceAlerts>)

  vi.mocked(useBtcPriceSnapshotQuery).mockReturnValue({
    data: { currentPrice: 64_213.5 } as Partial<BtcPriceSnapshot>,
  } as ReturnType<typeof useBtcPriceSnapshotQuery>)

  vi.mocked(macroAlertApi.getUpcomingEvents).mockResolvedValue(macroEvents)
  vi.mocked(macroAlertApi.getSubscriptions).mockResolvedValue([])

  return renderWithQuery(<AlertManagement userId={defaultUserId} />)
}

export async function clickNewAlert(user: UserEvent) {
  await user.click(screen.getByRole('button', { name: 'Create alert' }))
}

export async function openTab(user: UserEvent, label: RegExp) {
  await user.click(screen.getByRole('button', { name: label }))
}

export function getFilterButton(label: string) {
  return screen.getByRole('button', { name: new RegExp(`^${label} \\(\\d+\\)$`) })
}

export function expectFilterCount(label: string, count: number) {
  expect(getFilterButton(label)).toHaveAccessibleName(`${label} (${count})`)
}

export async function chooseAlertType(user: UserEvent, label: RegExp) {
  await user.click(screen.getByRole('button', { name: label }))
}

export async function switchAlertTypeTo(user: UserEvent, label: string) {
  await user.click(screen.getByRole('button', { name: label, pressed: false }))
}
