import { render, screen } from '@testing-library/react'
import { expect } from 'vitest'
import { PriceStreamStatus } from '@/components/dashboard/price/PriceStreamStatus'

export function renderPriceStreamStatus() {
  return render(<PriceStreamStatus />)
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
