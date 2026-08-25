import { screen } from '@testing-library/react'
import type { UserEvent } from '@testing-library/user-event'
import { expect } from 'vitest'
import { MacroIndicatorsSection } from '@/components/dashboard/indicators/MacroIndicatorsSection'
import { TooltipProvider } from '@/components/ui/tooltip'
import { renderWithQuery } from '@/test/renderWithQuery'

export function renderSection(allowHistory = true) {
  return renderWithQuery(
    <TooltipProvider>
      <MacroIndicatorsSection allowHistory={allowHistory} />
    </TooltipProvider>,
  )
}

export async function selectHistoryView(user: UserEvent) {
  await user.click(screen.getByRole('button', { name: 'Historical' }))
}

export function expectCurrentView() {
  expect(screen.getByRole('button', { name: 'Current' })).toHaveAttribute(
    'aria-pressed',
    'true',
  )
}

export function expectHistoricalControls() {
  expect(screen.getByRole('button', { name: 'Historical' })).toHaveAttribute(
    'aria-pressed',
    'true',
  )
  expect(
    screen.getByRole('group', { name: 'Historical period' }),
  ).toBeInTheDocument()
}
