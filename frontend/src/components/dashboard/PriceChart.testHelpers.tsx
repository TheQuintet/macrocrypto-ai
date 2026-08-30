import { screen } from '@testing-library/react'
import { expect } from 'vitest'
import { PriceChart } from '@/components/dashboard/PriceChart'
import { renderWithQuery } from '@/test/renderWithQuery'

export function renderPriceChart() {
  return renderWithQuery(<PriceChart />)
}

export function expectNoChartTypeSwitcher() {
  expect(
    screen.queryByRole('group', { name: 'Chart type' }),
  ).not.toBeInTheDocument()
}
