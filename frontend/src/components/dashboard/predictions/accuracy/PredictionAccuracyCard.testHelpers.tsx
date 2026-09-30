import { screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { expect } from 'vitest'
import { PredictionAccuracyCard } from '@/components/dashboard/predictions/accuracy/PredictionAccuracyCard'
import { renderWithQuery } from '@/test/renderWithQuery'

export function renderAccuracyCard() {
  return renderWithQuery(<PredictionAccuracyCard />)
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

/** The shared dialog has no accessible name, so find it by its heading. */
export async function openDetails() {
  await userEvent.click(screen.getByRole('button', { name: 'View details' }))
  const dialog = await screen.findByRole('dialog')

  expect(
    within(dialog).getByRole('heading', { name: 'Forecast accuracy details' }),
  ).toBeInTheDocument()
  return dialog
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
