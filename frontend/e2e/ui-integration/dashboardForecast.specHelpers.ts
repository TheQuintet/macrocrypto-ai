import { expect, type Page } from '@playwright/test'
import { routes } from '../../src/constants/navigation'

const CARD_TITLE = 'Next 24 hours'

/** The forecast card, found by its title so other dashboard cards stay out. */
export function getForecastCard(page: Page) {
  return page.locator('[data-slot="card"]').filter({
    has: page.locator('[data-slot="card-title"]', { hasText: CARD_TITLE }),
  })
}

export function getForecastChart(page: Page) {
  return getForecastCard(page).getByRole('img', {
    name: 'BTC 24h price forecast',
  })
}

function getForecastsLink(page: Page) {
  return getForecastCard(page).getByRole('link', { name: 'Open forecasts' })
}

function getPredictedFigure(page: Page) {
  return getForecastCard(page).getByRole('group', {
    name: 'Predicted in 24 hours',
    exact: true,
  })
}

export async function expectForecastCardRendered(page: Page) {
  await expect(getForecastCard(page)).toBeVisible()
  await expect(getForecastChart(page)).toBeVisible()
}

/** Actual candles, then the dashed forecast line and its shaded band. */
export async function expectActualThenForecast(page: Page) {
  const chart = getForecastChart(page)
  const band = chart.locator('.recharts-area-area')
  const line = chart.locator('.recharts-line-curve')
  const candles = chart.locator('.recharts-bar-rectangle')

  await expect(candles.first()).toBeVisible()
  await expect(band).toHaveAttribute('d', /^M/)
  await expect(line).toHaveCount(1)
  await expect(line).toHaveAttribute('stroke-dasharray', '5 4')
  await expect(chart.getByText('forecast start', { exact: true })).toBeVisible()

  const lineBox = await line.boundingBox()
  const firstCandleBox = await candles.first().boundingBox()
  expect(lineBox).not.toBeNull()
  expect(firstCandleBox).not.toBeNull()
  expect(lineBox!.x).toBeGreaterThan(firstCandleBox!.x)
}

/** The headline figures beside the chart, with coverage read as a range. */
export async function expectForecastFigures(page: Page) {
  const card = getForecastCard(page)
  const figure = (label: string) =>
    card.getByRole('group', { name: label, exact: true })

  await expect(getPredictedFigure(page)).toContainText(/\$[\d,]+\.\d{2}/)
  await expect(figure('Expected change')).toContainText(/[+-]?\d+\.\d{2}%/)
  await expect(figure('Range coverage')).toContainText('85% range')
  await expect(figure('Expected high')).toContainText(/\$[\d,]+\.\d{2}/)
  await expect(figure('Expected low')).toContainText(/\$[\d,]+\.\d{2}/)
  await expect(card.getByLabel(/^Trend (up|down|neutral)$/)).toBeVisible()
  await expect(card.getByText(/^Forecast made .+ \(.+\)\./)).toBeVisible()
}

export async function openForecasts(page: Page) {
  await getForecastsLink(page).click()
}

export async function expectOnForecastsPage(page: Page) {
  await expect(page).toHaveURL(new RegExp(`${routes.forecasts}$`))
  await expect(
    page.getByRole('group', { name: 'Forecast horizon', exact: true }),
  ).toBeVisible()
}

/** Tall enough to hit reliably on a phone. */
export async function expectLinkTappable(page: Page) {
  const box = await getForecastsLink(page).boundingBox()

  expect(box?.height ?? 0).toBeGreaterThanOrEqual(40)
}

/** The chart fits the viewport and the figures sit below it, not beside it. */
export async function expectStackedWithinViewport(page: Page) {
  const viewportWidth = page.viewportSize()?.width ?? 0
  const chartBox = await getForecastChart(page).boundingBox()
  const figuresBox = await getPredictedFigure(page).boundingBox()

  expect(chartBox).not.toBeNull()
  expect(figuresBox).not.toBeNull()
  expect(chartBox!.x + chartBox!.width).toBeLessThanOrEqual(viewportWidth)
  expect(figuresBox!.y).toBeGreaterThan(chartBox!.y + chartBox!.height)
}

/** On a wide screen the figures sit beside the chart. */
export async function expectFiguresBesideChart(page: Page) {
  const chartBox = await getForecastChart(page).boundingBox()
  const figuresBox = await getPredictedFigure(page).boundingBox()

  expect(chartBox).not.toBeNull()
  expect(figuresBox).not.toBeNull()
  expect(figuresBox!.x).toBeGreaterThan(chartBox!.x + chartBox!.width)
}

/**
 * Touch the forecast half of the plot, as a phone would. On a phone the card
 * sits below the price cards, so it is scrolled into view first: a tap at
 * off-screen coordinates lands on nothing.
 */
export async function tapForecast(page: Page) {
  const chart = getForecastChart(page)
  await chart.scrollIntoViewIfNeeded()
  const box = await chart.boundingBox()
  if (!box) throw new Error('forecast chart has no bounding box')

  await page.touchscreen.tap(box.x + box.width * 0.8, box.y + box.height / 2)
}

export async function expectForecastTooltip(page: Page) {
  const tooltip = page.getByRole('tooltip')

  await expect(tooltip).toBeVisible()
  await expect(tooltip).toContainText('Predicted')
  await expect(tooltip).toContainText('Upper bound')
}
