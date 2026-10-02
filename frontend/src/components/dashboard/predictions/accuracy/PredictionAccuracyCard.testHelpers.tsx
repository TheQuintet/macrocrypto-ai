import { QueryClientProvider, type QueryClient } from '@tanstack/react-query'
import { act, render, screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { expect } from 'vitest'
import { PredictionAccuracyCard } from '@/components/dashboard/predictions/accuracy/PredictionAccuracyCard'
import { createTestQueryClient } from '@/test/renderWithQuery'

/** Returns the query client too, so a spec can make the card refetch. */
export function renderAccuracyCard() {
  const client = createTestQueryClient()
  render(
    <QueryClientProvider client={client}>
      <PredictionAccuracyCard />
    </QueryClientProvider>,
  )
  return { client }
}

/** What the next scheduled fetch does: refetch every accuracy query. */
export async function refetchAccuracy(client: QueryClient) {
  await act(() => client.invalidateQueries())
}

function getScore() {
  return screen.getByRole('group', { name: 'Accuracy score' })
}

export async function expectScore(value: string, caption: string | RegExp) {
  await waitFor(() => {
    expect(within(getScore()).getByText(value)).toBeInTheDocument()
  })
  expect(within(getScore()).getByText(caption)).toBeInTheDocument()
}

export function expectScoreLabel(label: string) {
  expect(within(getScore()).getByText(label)).toBeInTheDocument()
}

export function expectAccuracyStat(label: string, value: string | RegExp) {
  expect(
    within(screen.getByRole('group', { name: label })).getByText(value),
  ).toBeInTheDocument()
}

export function expectWarning(message: string | RegExp) {
  const warning = screen.getByRole('status', { name: 'Accuracy warning' })

  expect(within(warning).getByText(message)).toBeInTheDocument()
}

export function expectNoWarning() {
  expect(
    screen.queryByRole('status', { name: 'Accuracy warning' }),
  ).not.toBeInTheDocument()
}

export function expectTrendChart() {
  expect(
    screen.getByRole('img', { name: 'Forecast accuracy trend' }),
  ).toBeInTheDocument()
}

export function expectSimulatedBadge() {
  expect(screen.getByText('Simulated')).toBeInTheDocument()
}

export function expectNoSimulatedBadge() {
  expect(screen.queryByText('Simulated')).not.toBeInTheDocument()
}

export function expectDescription(text: string | RegExp) {
  expect(screen.getByText(text)).toBeInTheDocument()
}

/** The dialog is named by its title. */
export async function openDetails() {
  await userEvent.click(screen.getByRole('button', { name: 'View details' }))
  return screen.findByRole('dialog', { name: 'Forecast accuracy details' })
}

export function expectDetailsDescribed(text: string | RegExp) {
  expect(
    screen.getByRole('dialog', { name: 'Forecast accuracy details' }),
  ).toHaveAccessibleDescription(text)
}

export function expectFocusBackOnViewDetails() {
  expect(screen.getByRole('button', { name: 'View details' })).toHaveFocus()
}

export function expectBreakdownRow(
  dialog: HTMLElement,
  market: string,
  cells: string[],
) {
  const table = within(dialog).getByRole('table', {
    name: 'Accuracy by market condition',
  })
  const row = within(table).getByRole('row', { name: new RegExp(market) })

  for (const cell of cells) {
    expect(within(row).getByText(cell)).toBeInTheDocument()
  }
}

export function expectCheckStatus(
  dialog: HTMLElement,
  check: string,
  status: string,
) {
  const table = within(dialog).getByRole('table', { name: 'Quality checks' })
  const row = within(table).getByRole('row', { name: new RegExp(check) })

  expect(within(row).getByText(status)).toBeInTheDocument()
}

export async function expectUnavailable(message: string) {
  const alert = await screen.findByRole('alert')

  expect(within(alert).getByText('Accuracy unavailable')).toBeInTheDocument()
  expect(within(alert).getByText(message)).toBeInTheDocument()
}

export async function expectNothingScoredYet() {
  expect(
    await screen.findByText(
      'No forecasts have been scored for this horizon yet',
    ),
  ).toBeInTheDocument()
}

export function expectMetricTone(
  dialog: HTMLElement,
  value: string,
  tone: string,
) {
  expect(within(dialog).getAllByText(value)[0]).toHaveClass(tone)
}

export async function closeDetails(dialog: HTMLElement) {
  await userEvent.click(within(dialog).getByRole('button', { name: 'Close' }))
}

export function expectDetailsClosed() {
  expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
}

export function expectScoreTone(value: string, tone: string) {
  expect(within(getScore()).getByText(value)).toHaveClass(tone)
}

export function expectStatTone(label: string, value: string, tone: string) {
  expect(
    within(screen.getByRole('group', { name: label })).getByText(value),
  ).toHaveClass(tone)
}

export function expectStatUntoned(label: string, value: string) {
  const figure = within(screen.getByRole('group', { name: label })).getByText(
    value,
  )

  expect(figure).not.toHaveClass('text-positive')
  expect(figure).not.toHaveClass('text-warning')
}

export function expectTrendLines(labels: string[]) {
  const legend = screen.getByRole('group', { name: 'Accuracy trend legend' })

  for (const label of labels) {
    expect(within(legend).getByText(label, { exact: false })).toBeInTheDocument()
  }
}

export async function expectTrendLineCount(count: number) {
  await waitFor(() => {
    const legend = screen.getByRole('group', { name: 'Accuracy trend legend' })
    expect(
      within(legend).getAllByText(/^(24h|7d) forecasts/),
    ).toHaveLength(count)
  })
}

export function expectTrendCaption(text: string | RegExp) {
  expect(screen.getByText(text)).toBeInTheDocument()
}

export async function expectTrendGapNote(text: string) {
  expect(await screen.findByText(text)).toBeInTheDocument()
}

export async function showComparison() {
  await userEvent.click(
    within(screen.getByRole('group', { name: 'Accuracy chart' })).getByRole(
      'button',
      { name: 'Predicted vs actual' },
    ),
  )
}

export async function expectComparisonChart(horizon: string) {
  expect(
    await screen.findByRole('img', {
      name: `Predicted vs actual BTC price, ${horizon} forecasts`,
    }),
  ).toBeInTheDocument()
  expect(
    screen.getByRole('group', { name: 'Predicted vs actual legend' }),
  ).toHaveTextContent('Predicted priceActual price')
}

export async function expectComparisonUnavailable(message: string) {
  const alert = await screen.findByRole('alert')

  expect(within(alert).getByText('Comparison unavailable')).toBeInTheDocument()
  expect(within(alert).getByText(message)).toBeInTheDocument()
}

export async function expectNoComparisonScored(horizon: string) {
  expect(
    await screen.findByText(`No ${horizon} forecasts scored yet`),
  ).toBeInTheDocument()
}

export async function expectDialogTrend(dialog: HTMLElement) {
  expect(
    within(dialog).getByRole('img', { name: 'Forecast accuracy trend' }),
  ).toBeInTheDocument()
  expect(
    within(dialog).getByRole('group', { name: 'Accuracy trend legend' }),
  ).toBeInTheDocument()
}

export async function expectDialogComparison(
  dialog: HTMLElement,
  horizon: string,
) {
  expect(
    await within(dialog).findByRole('img', {
      name: `Predicted vs actual BTC price, ${horizon} forecasts`,
    }),
  ).toBeInTheDocument()
}

/** A `dt`/`dd` pair in the scorecard. */
export function expectDialogFact(
  dialog: HTMLElement,
  label: string,
  value: string | RegExp,
) {
  const term = within(dialog).getByText(label, { selector: 'dt' })

  expect(term.nextElementSibling).toHaveTextContent(value)
}

export function expectNoTrainingDate(dialog: HTMLElement) {
  expect(within(dialog).queryByText(/train/i)).not.toBeInTheDocument()
}

export function expectBreakdownGrade(
  dialog: HTMLElement,
  market: string,
  value: string,
  tone: string,
) {
  const table = within(dialog).getByRole('table', {
    name: 'Accuracy by market condition',
  })
  const row = within(table).getByRole('row', { name: new RegExp(market) })

  expect(within(row).getByText(value)).toHaveClass(tone)
}

export function expectBreakdownUngraded(
  dialog: HTMLElement,
  market: string,
  value: string,
) {
  const table = within(dialog).getByRole('table', {
    name: 'Accuracy by market condition',
  })
  const cell = within(
    within(table).getByRole('row', { name: new RegExp(market) }),
  ).getByText(value)

  expect(cell).not.toHaveClass('text-positive')
  expect(cell).not.toHaveClass('text-warning')
}

/** The comparison's own copy of the 24h/7d toggle. */
export async function selectComparisonHorizon(label: string) {
  await userEvent.click(
    within(
      screen.getByRole('group', { name: 'Comparison horizon' }),
    ).getByRole('button', { name: label }),
  )
}

export async function zoomComparison(direction: 'in' | 'out') {
  await userEvent.click(
    within(screen.getByRole('group', { name: 'Comparison zoom' })).getByRole(
      'button',
      { name: direction === 'in' ? 'Zoom in' : 'Zoom out' },
    ),
  )
}

export async function expectComparisonSpan(text: string) {
  expect(await screen.findByText(text)).toBeInTheDocument()
}

export function expectComparisonZoomOutDisabled() {
  expect(
    within(screen.getByRole('group', { name: 'Comparison zoom' })).getByRole(
      'button',
      { name: 'Zoom out' },
    ),
  ).toBeDisabled()
}

/** A market tile on the card: its accuracy figure and the colour it is graded. */
export function expectMarketTile(market: string, value: string, tone: string) {
  const tile = screen.getByRole('group', { name: market })

  expect(within(tile).getByText(value)).toHaveClass(tone)
}

export function expectMarketTileUngraded(market: string, value: string) {
  const figure = within(screen.getByRole('group', { name: market })).getByText(
    value,
  )

  for (const tone of ['text-positive', 'text-warning', 'text-negative']) {
    expect(figure).not.toHaveClass(tone)
  }
}

export function expectMarketGradeLegend(text: string | RegExp) {
  expect(
    within(
      screen.getByRole('region', { name: 'Accuracy by market' }),
    ).getByText(text),
  ).toBeInTheDocument()
}

/** Amber panel with the warning triangle, so it reads without the words. */
export function expectWarningStyled() {
  const warning = screen.getByRole('status', { name: 'Accuracy warning' })

  expect(warning).toHaveClass('border-warning/40', 'bg-warning/10')
  expect(warning.querySelector('svg')).toHaveClass('text-warning')
}

export async function expectWarningCleared() {
  await waitFor(() => {
    expectNoWarning()
  })
}
