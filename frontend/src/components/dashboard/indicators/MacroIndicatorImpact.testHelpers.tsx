import { render, screen } from '@testing-library/react'
import type { UserEvent } from '@testing-library/user-event'
import { expect } from 'vitest'
import { MacroIndicatorImpact } from '@/components/dashboard/indicators/MacroIndicatorImpact'
import { TooltipProvider } from '@/components/ui/tooltip'

export function renderImpact(indicatorName: string, changePercent: number | null) {
  return render(
    <TooltipProvider>
      <MacroIndicatorImpact
        indicatorName={indicatorName}
        changePercent={changePercent}
      />
    </TooltipProvider>,
  )
}

export function getImpactTrigger() {
  return screen.getByRole('button')
}

export async function openImpactTooltip(user: UserEvent) {
  await user.hover(getImpactTrigger())
  await screen.findAllByRole('tooltip')
}

export function expectTooltipCopy(text: string | RegExp) {
  expect(screen.getAllByText(text).length).toBeGreaterThan(0)
}
