import { render } from '@testing-library/react'
import { expect } from 'vitest'
import { MarketConditionIcon } from '@/components/dashboard/predictions/accuracy/MarketConditionIcon'
import type { MarketCondition } from '@/types/predictionAccuracy'

export function renderMarketIcon(condition: MarketCondition) {
  const { container } = render(<MarketConditionIcon condition={condition} />)
  return container.querySelector('svg')
}

/** The icon names the market by shape, so it stays out of the colour grading. */
export function expectNeutralDecorativeIcon(icon: Element | null) {
  expect(icon).not.toBeNull()
  expect(icon).toHaveAttribute('aria-hidden', 'true')
  expect(icon).toHaveClass('text-muted-foreground')
  expect(icon).not.toHaveClass('text-positive')
  expect(icon).not.toHaveClass('text-negative')
}
