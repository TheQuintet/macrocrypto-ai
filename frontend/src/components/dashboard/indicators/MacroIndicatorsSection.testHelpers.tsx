import { screen } from '@testing-library/react'
import { expect } from 'vitest'
import { MacroIndicatorsSection } from '@/components/dashboard/indicators/MacroIndicatorsSection'
import { TooltipProvider } from '@/components/ui/tooltip'
import { renderWithQuery } from '@/test/renderWithQuery'

export function renderSection() {
  return renderWithQuery(
    <TooltipProvider>
      <MacroIndicatorsSection />
    </TooltipProvider>,
  )
}

export function expectHistoryOnPage() {
  expect(
    screen.queryByRole('group', { name: 'Historical period' }),
  ).not.toBeInTheDocument()
  expect(screen.getByText('Indicator history')).toBeInTheDocument()
}
