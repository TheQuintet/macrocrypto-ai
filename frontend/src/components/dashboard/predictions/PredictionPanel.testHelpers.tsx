import { screen, waitFor, within } from '@testing-library/react'
import { expect } from 'vitest'
import { PredictionPanel } from '@/components/dashboard/predictions/PredictionPanel'
import { renderWithQuery } from '@/test/renderWithQuery'

export function renderPanel() {
  return renderWithQuery(<PredictionPanel />)
}

export async function expectChartRendered(horizon: string) {
  await waitFor(() => {
    expect(
      screen.getByRole('img', { name: `BTC ${horizon} price forecast` }),
    ).toBeInTheDocument()
  })
}

export async function expectSummaryValue(label: string, value: string) {
  await waitFor(() => {
    expect(
      within(screen.getByRole('group', { name: label })).getByText(value),
    ).toBeInTheDocument()
  })
}

export async function expectRangeCoverage(percent: string) {
  await waitFor(() => {
    const meter = screen.getByRole('meter', { name: 'Range coverage' })

    expect(screen.getByText(`${percent} range`)).toBeInTheDocument()
    expect(meter).toHaveAttribute('aria-valuenow', percent.replace('%', ''))
  })
}

/** The batch timestamp, so an old forecast is not read as a current one. */
export function expectForecastMadeAt(isoTime: string) {
  const time = screen.getByText(
    (_, element) =>
      element?.tagName === 'TIME' &&
      element.getAttribute('dateTime') === isoTime,
  )

  expect(time.closest('p')).toHaveTextContent(/^Forecast made .+ ago \(/)
}

export function expectSimulatedBadge() {
  expect(screen.getByText('Simulated')).toBeInTheDocument()
}

export function expectNoSimulatedBadge() {
  expect(screen.queryByText('Simulated')).not.toBeInTheDocument()
}

export function expectLegendExplains(confidenceLabel: string) {
  const legend = screen.getByRole('group', { name: 'Chart legend' })

  expect(
    within(legend).getByText(`${confidenceLabel} confidence band`),
  ).toBeInTheDocument()
  expect(
    within(legend).getByText(
      new RegExp(
        `${confidenceLabel} confidence: price is expected to fall within`,
        'i',
      ),
    ),
  ).toBeInTheDocument()
}

export async function expectForecastUnavailable(message: string) {
  await waitFor(() => {
    expect(screen.getAllByRole('alert').length).toBeGreaterThan(0)
  })
  expect(screen.getAllByText('Forecast unavailable').length).toBeGreaterThan(0)
  expect(screen.getAllByText(message).length).toBeGreaterThan(0)
}
