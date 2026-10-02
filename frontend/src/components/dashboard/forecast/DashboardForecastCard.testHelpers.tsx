import { QueryClientProvider, type QueryClient } from '@tanstack/react-query'
import { render, screen, waitFor, within } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { expect } from 'vitest'
import { btcPredictionQueryKey } from '@/api/predictions/btcPrediction'
import { DashboardForecastCard } from '@/components/dashboard/forecast/DashboardForecastCard'
import { usePredictionStore } from '@/stores/predictionStore'
import { createTestQueryClient } from '@/test/renderWithQuery'
import type { PredictionHorizon, PredictionParams } from '@/types/predictions'

/** Renders the card and hands back its client, so the cache can be inspected. */
export function renderDashboardForecast(
  client: QueryClient = createTestQueryClient(),
) {
  render(
    <QueryClientProvider client={client}>
      <MemoryRouter>
        <DashboardForecastCard />
      </MemoryRouter>
    </QueryClientProvider>,
  )

  return client
}

export function getForecastChart(horizon: PredictionHorizon = '24h') {
  return screen.getByRole('img', { name: `BTC ${horizon} price forecast` })
}

export async function expectForecastChart(horizon: PredictionHorizon = '24h') {
  await waitFor(() => {
    expect(getForecastChart(horizon)).toBeInTheDocument()
  })
}

/** The dashed forecast line and its shaded band, drawn as paths. */
export function expectForecastPathAndBand() {
  const chart = getForecastChart()
  const line = chart.querySelector('.recharts-line-curve')
  const band = chart.querySelector('.recharts-area-area')

  expect(line).not.toBeNull()
  expect(line).toHaveAttribute('stroke-dasharray', '5 4')
  expect(band?.getAttribute('d')).toMatch(/^M/)
}

export function expectCandlesDrawn() {
  expect(
    getForecastChart().querySelectorAll('.recharts-bar-rectangle').length,
  ).toBeGreaterThan(0)
}

export function expectNoCandlesDrawn() {
  expect(
    getForecastChart().querySelectorAll('.recharts-bar-rectangle'),
  ).toHaveLength(0)
}

/** The legend names actual price only when candles are on the plot. */
export function expectLegendNames(marks: string[]) {
  const legend = screen.getByRole('group', { name: 'Chart legend' })

  for (const mark of marks) {
    expect(within(legend).getByText(mark, { exact: false })).toBeInTheDocument()
  }
}

export function expectLegendOmits(mark: string) {
  expect(
    within(screen.getByRole('group', { name: 'Chart legend' })).queryByText(
      mark,
    ),
  ).not.toBeInTheDocument()
}

export function expectFigure(label: string, value: string | RegExp) {
  expect(screen.getByRole('group', { name: label })).toHaveTextContent(value)
}

export function expectTrend(label: 'up' | 'down' | 'neutral') {
  expect(screen.getByLabelText(`Trend ${label}`)).toBeInTheDocument()
}

export function expectRangeCoverage(percent: string) {
  expectFigure('Range coverage', `${percent} range`)
}

export function expectForecastMadeAt(isoTime: string) {
  const time = screen.getByText(
    (_, element) =>
      element?.tagName === 'TIME' &&
      element.getAttribute('dateTime') === isoTime,
  )

  expect(time.closest('p')).toHaveTextContent(/^Forecast made .+ ago \(/)
}

export function expectForecastsLink(href: string) {
  expect(screen.getByRole('link', { name: 'Open forecasts' })).toHaveAttribute(
    'href',
    href,
  )
}

export function expectSimulatedBadge() {
  expect(screen.getByText('Simulated')).toBeInTheDocument()
}

export function expectNoSimulatedBadge() {
  expect(screen.queryByText('Simulated')).not.toBeInTheDocument()
}

/** The skeleton stands in for the chart, with no figures yet. */
export function expectLoading() {
  expect(document.querySelector('[data-slot="skeleton"]')).not.toBeNull()
  expect(screen.queryByRole('img')).not.toBeInTheDocument()
}

export async function expectForecastUnavailable(message: string) {
  const alert = await screen.findByRole('alert')

  expect(alert).toHaveTextContent('Forecast unavailable')
  expect(alert).toHaveTextContent(message)
  expect(screen.queryByRole('img')).not.toBeInTheDocument()
}

export function expectCachedUnder(client: QueryClient, params: PredictionParams) {
  expect(client.getQueryData(btcPredictionQueryKey(params))).toBeDefined()
}

export function expectStoreHorizon(horizon: PredictionHorizon) {
  expect(usePredictionStore.getState().horizon).toBe(horizon)
}
