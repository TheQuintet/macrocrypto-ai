import { render, screen, within } from '@testing-library/react'
import type { UserEvent } from '@testing-library/user-event'
import { expect, vi } from 'vitest'
import { MacroCalendarTable } from './MacroCalendarTable'
import { macroEvents } from './MacroAlertForm.testHelpers'
import type { MacroEventSubscription } from '@/hooks/alerts/useMacroEvents'
import type {
  EventImpact,
  EventType,
  MacroEvent,
  MacroEventStatusFilter,
} from '@/types/alerts/macroAlert'

/** FED is subscribed with a one-time alert; CPI has no alert. */
export const subscribedEvents: MacroEvent[] = [
  { ...macroEvents[0], subscribed: true },
  { ...macroEvents[1], subscribed: false },
]

export const subscriptionMap = new Map<EventType, MacroEventSubscription>([
  ['FED', { timing: '1D', oneTime: true }],
])

type TableProps = {
  events?: MacroEvent[]
  subscriptions?: Map<EventType, MacroEventSubscription>
  isLoading?: boolean
  error?: string | null
  filter?: MacroEventStatusFilter
  impactFilter?: EventImpact | 'all'
}

export function renderMacroTable(overrides: TableProps = {}) {
  const onSubscribeChange = vi.fn()
  const onDelete = vi.fn()
  const onEdit = vi.fn()
  const onRetry = vi.fn()

  const view = render(
    <MacroCalendarTable
      events={overrides.events ?? subscribedEvents}
      subscriptions={overrides.subscriptions ?? subscriptionMap}
      isLoading={overrides.isLoading ?? false}
      error={overrides.error ?? null}
      filter={overrides.filter ?? 'all'}
      impactFilter={overrides.impactFilter ?? 'all'}
      onSubscribeChange={onSubscribeChange}
      onDelete={onDelete}
      onEdit={onEdit}
      onRetry={onRetry}
    />,
  )

  return { ...view, onSubscribeChange, onDelete, onEdit, onRetry }
}

export function getEventRow(name: string) {
  const row = screen.getByText(name).closest('tr')
  if (!row) throw new Error(`No table row for "${name}"`)
  return row as HTMLElement
}

export function getRowDeleteButton(name: string) {
  return within(getEventRow(name)).getByRole('button', { name: 'Delete alert' })
}

export async function toggleRowStatus(user: UserEvent, name: string, label: string) {
  await user.click(within(getEventRow(name)).getByRole('switch', { name: label }))
}

export async function deleteRowAlert(user: UserEvent, name: string) {
  await user.click(getRowDeleteButton(name))
  await user.click(screen.getByRole('button', { name: 'Delete' }))
}

export function expectRowText(name: string, text: string) {
  expect(getEventRow(name)).toHaveTextContent(text)
}

export async function clickRow(user: UserEvent, name: string) {
  await user.click(within(getEventRow(name)).getByText(name))
}
