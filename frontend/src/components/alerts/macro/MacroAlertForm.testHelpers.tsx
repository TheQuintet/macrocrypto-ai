import { render, screen } from '@testing-library/react'
import type { UserEvent } from '@testing-library/user-event'
import { expect, vi } from 'vitest'
import { MacroAlertForm } from './MacroAlertForm'
import type { MacroAlertDraft, MacroEvent } from '@/types/alerts/macroAlert'

export const macroEvents: MacroEvent[] = [
  {
    id: 'event-fed',
    event_id: 'fed-1',
    event_type: 'FED',
    event_name: 'FOMC Rate Decision',
    description: 'Federal funds rate announcement',
    scheduled_at: '2026-09-17T18:00:00.000Z',
    timezone: 'UTC',
    impact: 'HIGH',
    subscribed: false,
    notified: false,
  },
  {
    id: 'event-cpi',
    event_id: 'cpi-1',
    event_type: 'CPI',
    event_name: 'CPI Release',
    description: 'Consumer price index',
    scheduled_at: '2026-09-10T12:30:00.000Z',
    timezone: 'UTC',
    impact: 'MEDIUM',
    subscribed: false,
    notified: false,
  },
]

type FormProps = {
  open?: boolean
  onOpenChange?: (open: boolean) => void
  events?: MacroEvent[]
  onSubmit?: (draft: MacroAlertDraft) => void
  isLoading?: boolean
}

export function renderMacroForm(overrides: FormProps = {}) {
  const onSubmit = overrides.onSubmit ?? vi.fn()
  const onOpenChange = overrides.onOpenChange ?? vi.fn()

  const view = render(
    <MacroAlertForm
      open={overrides.open ?? true}
      onOpenChange={onOpenChange}
      events={overrides.events ?? macroEvents}
      onSubmit={onSubmit}
      isLoading={overrides.isLoading ?? false}
    />,
  )

  return { ...view, onSubmit, onOpenChange }
}

export function getCreateButton() {
  return screen.getByRole('button', { name: 'Create alert' })
}

export async function selectMacroEvent(user: UserEvent, label: string) {
  await user.click(screen.getByRole('button', { name: /^Event/ }))
  await user.click(screen.getByRole('button', { name: new RegExp(label) }))
}

export async function selectNotifyBy(user: UserEvent, label: string) {
  await user.click(screen.getByRole('button', { name: 'Notify by' }))
  await user.click(screen.getByRole('button', { name: label }))
}

export function getRequiredSection() {
  return screen.getByRole('region', { name: 'Required' })
}

export function getAdvancedToggle() {
  return screen.getByRole('button', { name: 'Advanced' })
}

export async function openAdvanced(user: UserEvent) {
  await user.click(getAdvancedToggle())
}

export function expectAdvancedOpen() {
  expect(getAdvancedToggle()).toHaveAttribute('aria-expanded', 'true')
}

export async function toggleNamedSwitch(user: UserEvent, name: string) {
  await user.click(screen.getByRole('switch', { name }))
}

export async function submitMacroForm(user: UserEvent) {
  await user.click(getCreateButton())
}

export function expectValidationError(text: string) {
  expect(screen.getByText(text)).toBeInTheDocument()
}
