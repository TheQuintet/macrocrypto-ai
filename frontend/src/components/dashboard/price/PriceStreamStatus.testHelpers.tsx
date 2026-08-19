import { render, screen } from '@testing-library/react'
import type { UserEvent } from '@testing-library/user-event'
import { expect } from 'vitest'
import { PriceStreamStatus } from '@/components/dashboard/price/PriceStreamStatus'
import { TooltipProvider } from '@/components/ui/tooltip'

export function renderPriceStreamStatus() {
  return render(
    <TooltipProvider>
      <PriceStreamStatus />
    </TooltipProvider>,
  )
}

export function getStatusIndicator() {
  return screen.getByRole('status')
}

export function expectStatusIndicator(label: string, tone: string) {
  const indicator = getStatusIndicator()
  expect(indicator).toHaveTextContent(label)
  expect(indicator).toHaveAttribute('aria-label', `Price feed ${label}`)
  expect(indicator).toHaveClass(tone)
}

export function expectLastUpdated(text: string) {
  expect(screen.getByText(`Updated ${text}`)).toBeInTheDocument()
}

export async function openStatusTooltip(user: UserEvent) {
  await user.hover(getStatusIndicator())
  await screen.findAllByRole('tooltip')
}

/** Tooltip content is portalled and duplicated for a11y — match any copy. */
export function expectTooltipDetail(text: string | RegExp) {
  expect(screen.getAllByText(text).length).toBeGreaterThan(0)
}
