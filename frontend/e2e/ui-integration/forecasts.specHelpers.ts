import { expect, type Locator, type Page } from '@playwright/test'

export const HORIZON_GROUP = 'Forecast horizon'
export const CONFIDENCE_GROUP = 'Confidence level'

function getOption(page: Page, groupName: string, label: string) {
  return page
    .getByRole('group', { name: groupName, exact: true })
    .getByRole('button', { name: label, exact: true })
}

export function getChart(page: Page, horizon: string) {
  return page.getByRole('img', { name: `BTC ${horizon} price forecast` })
}

export function getSummaryStat(page: Page, label: string) {
  return page.getByRole('group', { name: label, exact: true })
}

export async function selectHorizon(page: Page, label: string) {
  await getOption(page, HORIZON_GROUP, label).click()
}

export async function selectConfidence(page: Page, label: string) {
  await getOption(page, CONFIDENCE_GROUP, label).click()
}

export async function expectHorizonSelected(page: Page, label: string) {
  await expect(getOption(page, HORIZON_GROUP, label)).toHaveAttribute(
    'aria-pressed',
    'true',
  )
}

export async function expectConfidenceSelected(page: Page, label: string) {
  await expect(getOption(page, CONFIDENCE_GROUP, label)).toHaveAttribute(
    'aria-pressed',
    'true',
  )
}

export async function expectChartRendered(page: Page, horizon: string) {
  await expect(getChart(page, horizon)).toBeVisible()
}

/** The band is the only filled area on the plot. */
export async function expectConfidenceBandRendered(page: Page, horizon: string) {
  const band = getChart(page, horizon).locator('.recharts-area-area')

  await expect(band).toBeVisible()
  await expect(band).toHaveAttribute('d', /^M/)
}

export async function expectPredictedLineRendered(page: Page, horizon: string) {
  await expect(
    getChart(page, horizon).locator('.recharts-line-curve').first(),
  ).toBeVisible()
}

export function getZoomControls(page: Page) {
  return page.getByRole('group', { name: 'Chart zoom' })
}

export async function zoomHistoryOut(page: Page) {
  await getZoomControls(page).getByRole('button', { name: 'Zoom out' }).click()
}

export async function zoomHistoryIn(page: Page) {
  await getZoomControls(page).getByRole('button', { name: 'Zoom in' }).click()
}

export async function candleCount(page: Page, horizon: string) {
  return getChart(page, horizon).locator('.recharts-bar-rectangle').count()
}

/**
 * Poll rather than sample: the previous window's candles stay on screen while
 * the new history query resolves, so a single read can catch the old count.
 */
export async function expectCandleCount(
  page: Page,
  horizon: string,
  count: number,
) {
  await expect
    .poll(() => candleCount(page, horizon), { timeout: 10_000 })
    .toBe(count)
}

export async function expectCandleCountAbove(
  page: Page,
  horizon: string,
  floor: number,
) {
  await expect
    .poll(() => candleCount(page, horizon), { timeout: 10_000 })
    .toBeGreaterThan(floor)
}

/** At rest the window matches the label, so zooming in is already at its stop. */
export async function expectZoomInDisabled(page: Page) {
  await expect(
    getZoomControls(page).getByRole('button', { name: 'Zoom in' }),
  ).toBeDisabled()
}

/** Candles only exist where real prices do — the history half of the plot. */
export async function expectCandlesRendered(page: Page, horizon: string) {
  const candles = getChart(page, horizon).locator('.recharts-bar-rectangle')

  await expect(candles.first()).toBeVisible()
  expect(await candles.count()).toBeGreaterThan(3)
}

/**
 * The endpoint returns forward points only, so the plot carries one model
 * line — the forecast — and it starts where the candles end, not under them.
 */
export async function expectForecastLineOnly(page: Page, horizon: string) {
  const chart = getChart(page, horizon)
  const curves = chart.locator('.recharts-line-curve')

  await expect(curves).toHaveCount(1)

  const curveBox = await curves.first().boundingBox()
  const firstCandleBox = await chart
    .locator('.recharts-bar-rectangle')
    .first()
    .boundingBox()

  expect(curveBox).not.toBeNull()
  expect(firstCandleBox).not.toBeNull()
  expect(curveBox!.x).toBeGreaterThan(firstCandleBox!.x)
}

/**
 * The vertical divider marking the first forecast point. Labelled as the
 * forecast start, not "now": an older batch starts before the present.
 */
export async function expectForecastStartDivider(page: Page, horizon: string) {
  const chart = getChart(page, horizon)

  await expect(chart.locator('.recharts-reference-line')).toHaveCount(1)
  await expect(chart.getByText('forecast start', { exact: true })).toBeVisible()
  await expect(chart.getByText('now', { exact: true })).toHaveCount(0)
}

/** The batch timestamp, relative and absolute, under the chart. */
export async function expectForecastMadeAt(page: Page) {
  await expect(page.getByText(/^Forecast made .+ \(.+\)\./)).toBeVisible()
}

/** Every x-axis label, as rendered. */
export async function xAxisTickLabels(page: Page, horizon: string) {
  return getChart(page, horizon)
    .locator('.recharts-xAxis-tick-labels .recharts-cartesian-axis-tick-value')
    .allTextContents()
}

/**
 * A week of hourly points ticks by day, never by bare clock time. The month
 * may be three or four letters (`Sep` or `Sept`) depending on the ICU build.
 */
export async function expectDateTicks(page: Page, horizon: string) {
  await expect
    .poll(async () => (await xAxisTickLabels(page, horizon)).length)
    .toBeGreaterThan(1)

  for (const label of await xAxisTickLabels(page, horizon)) {
    expect(label).toMatch(/^\d{2} \w{3,4}$/)
  }
}

/**
 * The band's plotted path.
 *
 * Pixel height is not the measure here: the Y axis fits itself to the band, so
 * the shaded area covers a similar slice of the plot at every confidence
 * level. What changes is the prices it spans — see `keyLevelSpread`.
 */
export async function bandPath(page: Page, horizon: string) {
  return getChart(page, horizon)
    .locator('.recharts-area-area')
    .getAttribute('d')
}

function parsePrice(text: string) {
  return Number(text.replace(/[^0-9.]/g, ''))
}

/** Dollars between the window's expected high and low, as rendered. */
export async function keyLevelSpread(page: Page) {
  const levels = page.getByRole('group', {
    name: 'Confidence range',
    exact: true,
  })
  const high = await levels
    .getByRole('group', { name: 'Expected high', exact: true })
    .textContent()
  const low = await levels
    .getByRole('group', { name: 'Expected low', exact: true })
    .textContent()

  if (!high || !low) throw new Error('key levels are not rendered')

  return parsePrice(high.replace('Expected high', '')) -
    parsePrice(low.replace('Expected low', ''))
}

export async function expectSummaryStat(
  page: Page,
  label: string,
  value: string | RegExp,
) {
  await expect(getSummaryStat(page, label)).toContainText(value)
}

/** The selected level, read as the range it covers — not graded high or low. */
export async function expectRangeCoverage(page: Page, percent: string) {
  const meter = page.getByRole('meter', { name: 'Range coverage' })

  await expect(meter).toBeVisible()
  await expect(meter).toHaveAttribute('aria-valuenow', percent.replace('%', ''))
  await expect(page.getByText(`${percent} range`, { exact: true })).toBeVisible()
  await expect(
    page.getByText(`Price expected inside the band ${percent} of the time`),
  ).toBeVisible()
}

export async function expectCoverageLevels(page: Page) {
  const scale = page.getByRole('list', { name: 'Coverage levels' })

  for (const level of ['70%', '85%', '95%']) {
    await expect(scale.getByText(level, { exact: true })).toBeVisible()
  }
}

export async function expectLegendNames(page: Page, marks: string[]) {
  const legend = page.getByRole('group', { name: 'Chart legend' })

  for (const mark of marks) {
    await expect(legend).toContainText(mark)
  }
}

export async function expectLegendOmits(page: Page, mark: string) {
  await expect(
    page.getByRole('group', { name: 'Chart legend' }),
  ).not.toContainText(mark)
}

export async function expectLegendExplains(page: Page, confidence: string) {
  const legend = page.getByRole('group', { name: 'Chart legend' })

  await expect(legend).toContainText(`${confidence} confidence band`)
  await expect(legend).toContainText(
    `${confidence} confidence: price is expected to fall within this shaded range.`,
  )
}

export async function expectKeyLevels(page: Page, caption: RegExp) {
  const levels = page.getByRole('group', {
    name: 'Confidence range',
    exact: true,
  })

  await expect(levels).toContainText('Expected high')
  await expect(levels).toContainText('Expected low')
  await expect(levels).toContainText(caption)
}

export async function expectRangeWidthIndicator(page: Page) {
  await expect(
    page.getByRole('group', { name: 'Confidence range width' }),
  ).toContainText(/Narrow|Medium|Wide/)
}

async function hoverAcross(page: Page, horizon: string, fraction: number) {
  const box = await getChart(page, horizon).boundingBox()
  if (!box) throw new Error('forecast chart has no bounding box')

  await page.mouse.move(box.x + box.width * fraction, box.y + box.height / 2)
}

/** Hover the forecast half — the plot's centre is the forecast start itself. */
export async function hoverForecast(page: Page, horizon: string) {
  await hoverAcross(page, horizon, 0.8)
}

/** Hover the history half, where actual candles are. */
export async function hoverHistory(page: Page, horizon: string) {
  await hoverAcross(page, horizon, 0.25)
}

/** Touch the forecast half — how a phone reaches the same tooltip. */
export async function tapForecast(page: Page, horizon: string) {
  const box = await getChart(page, horizon).boundingBox()
  if (!box) throw new Error('forecast chart has no bounding box')

  await page.touchscreen.tap(box.x + box.width * 0.8, box.y + box.height / 2)
}

export async function expectPredictionTooltip(page: Page) {
  const tooltip = page.getByRole('tooltip')

  await expect(tooltip).toBeVisible()
  await expect(tooltip).toContainText('Predicted')
  await expect(tooltip).toContainText('Upper bound')
  await expect(tooltip).toContainText('Lower bound')
  await expect(tooltip).toContainText('Range width')
}

/** The history half reuses the dashboard's OHLC readout. */
export async function expectCandleTooltip(page: Page) {
  const tooltip = page.getByRole('tooltip')

  await expect(tooltip).toBeVisible()
  await expect(tooltip).toContainText('Open')
  await expect(tooltip).toContainText('Close')
}

export async function expectTooltipConfidence(page: Page, confidence: string) {
  await expect(page.getByRole('tooltip')).toContainText(
    `${confidence} confidence`,
  )
}

export function getAccuracyScore(page: Page) {
  return page.getByRole('group', { name: 'Accuracy score', exact: true })
}

/**
 * Price accuracy is the headline the service can produce today, explained
 * as how close forecasts landed rather than how often they were "right".
 */
export async function expectAccuracyScore(page: Page) {
  const score = getAccuracyScore(page)

  await expect(score).toContainText('Price accuracy')
  await expect(score).toContainText(/\d+%/)
  await expect(score).toContainText(
    /Forecasts were within \d+\.\d{2}% of the real price on average/,
  )
}

function getAccuracyTrend(scope: Page | Locator) {
  return scope.getByRole('img', { name: 'Forecast accuracy trend' })
}

/** Always both horizons, each named in the legend. */
export async function expectAccuracyTrend(scope: Page | Locator) {
  await expect(
    getAccuracyTrend(scope).locator('.recharts-line-curve'),
  ).toHaveCount(2)

  const legend = scope.getByRole('group', { name: 'Accuracy trend legend' })
  await expect(legend).toContainText('24h forecasts')
  await expect(legend).toContainText('7d forecasts')
}

/** The trend's lines, as drawn — unchanged by the horizon toggle. */
export async function accuracyTrendPaths(page: Page) {
  return getAccuracyTrend(page)
    .locator('.recharts-line-curve')
    .evaluateAll((paths) => paths.map((path) => path.getAttribute('d')))
}

/** The accuracy card sits below the fold; mouse and touch need it on screen. */
async function chartCentre(chart: Locator) {
  await chart.scrollIntoViewIfNeeded()
  const box = await chart.boundingBox()
  if (!box) throw new Error('chart has no bounding box')

  return { x: box.x + box.width * 0.6, y: box.y + box.height / 2 }
}

export async function hoverAccuracyTrend(page: Page) {
  const { x, y } = await chartCentre(getAccuracyTrend(page))
  await page.mouse.move(x, y)
}

/** Touch the trend — how a phone reaches the same tooltip. */
export async function tapAccuracyTrend(page: Page) {
  const { x, y } = await chartCentre(getAccuracyTrend(page))
  await page.touchscreen.tap(x, y)
}

export async function expectAccuracyTrendTooltip(page: Page) {
  const tooltip = page.getByRole('tooltip')

  await expect(tooltip).toBeVisible()
  await expect(tooltip).toContainText(/24h forecasts\d+%/)
  await expect(tooltip).toContainText(/7d forecasts\d+%/)
}

function getAccuracyComparison(scope: Page | Locator, horizon: string) {
  return scope.getByRole('img', {
    name: `Predicted vs actual BTC price, ${horizon} forecasts`,
  })
}

export async function showAccuracyComparison(page: Page) {
  await getOption(page, 'Accuracy chart', 'Predicted vs actual').click()
}

export async function expectAccuracyComparison(
  scope: Page | Locator,
  horizon: string,
) {
  await expect(
    getAccuracyComparison(scope, horizon).locator('.recharts-line-curve'),
  ).toHaveCount(2)
  await expect(
    scope.getByRole('group', { name: 'Predicted vs actual legend' }),
  ).toContainText('Predicted priceActual price')
}

/** The comparison's own copy of the 24h/7d toggle, beside the chart. */
export async function selectComparisonHorizon(page: Page, label: string) {
  await getOption(page, 'Comparison horizon', label).click()
}

export async function zoomAccuracyComparison(
  page: Page,
  direction: 'in' | 'out',
) {
  await page
    .getByRole('group', { name: 'Comparison zoom', exact: true })
    .getByRole('button', { name: direction === 'in' ? 'Zoom in' : 'Zoom out' })
    .click()
}

export async function accuracyComparisonSpanDays(page: Page) {
  const text = await page.getByText(/^Showing the last \d+ days?$/).textContent()
  const days = Number(text?.match(/\d+/)?.[0])
  if (!Number.isFinite(days)) throw new Error('comparison span is not shown')
  return days
}

export async function hoverAccuracyComparison(page: Page, horizon: string) {
  const { x, y } = await chartCentre(getAccuracyComparison(page, horizon))
  await page.mouse.move(x, y)
}

export async function expectAccuracyComparisonTooltip(page: Page) {
  const tooltip = page.getByRole('tooltip')

  await expect(tooltip).toBeVisible()
  await expect(tooltip).toContainText(/Predicted\$[\d,]+/)
  await expect(tooltip).toContainText(/Actual\$[\d,]+/)
  await expect(tooltip).toContainText(/Gap[+-]?\$[\d,]+ \([+-]?\d+\.\d{2}%\)/)
}

export async function expectAccuracyGrades(page: Page, horizon: string) {
  await expect(
    page.getByText(new RegExp(`past ${horizon} forecasts`)),
  ).toBeVisible()
}

export async function expectAccuracyWarning(page: Page) {
  await expect(
    page.getByRole('status', { name: 'Accuracy warning' }),
  ).toContainText('Average % miss has been above 10%')
}

export async function expectNoAccuracyWarning(page: Page) {
  await expect(
    page.getByRole('status', { name: 'Accuracy warning' }),
  ).toHaveCount(0)
}

const MARKETS = ['Bull market', 'Bear market', 'Volatile', 'Neutral']

const GRADE_CLASSES = {
  good: /\btext-positive\b/,
  medium: /\btext-warning\b/,
  poor: /\btext-negative\b/,
} as const

type MarketGrade = keyof typeof GRADE_CLASSES

function getMarketTile(page: Page, market: string) {
  return page
    .getByRole('region', { name: 'Accuracy by market' })
    .getByRole('group', { name: market, exact: true })
}

/** One tile per market, each with an accuracy % and its % miss. */
export async function expectMarketTiles(page: Page) {
  for (const market of MARKETS) {
    const tile = getMarketTile(page, market)
    await expect(tile).toContainText(/\d+%/)
    await expect(tile).toContainText(/\d+\.\d{2}% miss/)
  }
}

export async function expectMarketTileGraded(
  page: Page,
  market: string,
  grade: MarketGrade,
) {
  await expect(
    getMarketTile(page, market).getByText(/^\d+%$/),
  ).toHaveClass(GRADE_CLASSES[grade])
}

/** Two tiles a row on a phone: the third starts a new row under the first. */
export async function expectMarketTilesTwoByTwo(page: Page) {
  const boxes = await Promise.all(
    MARKETS.map((market) => getMarketTile(page, market).boundingBox()),
  )
  if (boxes.some((box) => box == null)) throw new Error('tile not rendered')
  const [first, second, third] = boxes as NonNullable<(typeof boxes)[number]>[]

  expect(Math.abs(first.y - second.y)).toBeLessThan(2)
  expect(third.y).toBeGreaterThan(first.y + first.height - 1)
  expect(Math.abs(third.x - first.x)).toBeLessThan(2)
}

/** On a small screen the score sits above the chart, not beside it. */
export async function expectAccuracyStacked(page: Page) {
  const score = await getAccuracyScore(page).boundingBox()
  const chart = await getAccuracyTrend(page).boundingBox()
  if (!score || !chart) throw new Error('accuracy card not rendered')

  expect(chart.y).toBeGreaterThan(score.y + score.height)
}

function getAccuracyDetails(page: Page) {
  return page.getByRole('dialog', { name: 'Forecast accuracy details' })
}

/** The dialog is named by its title. */
export async function openAccuracyDetails(page: Page) {
  await page.getByRole('button', { name: 'View details' }).click()
  const dialog = getAccuracyDetails(page)
  await expect(dialog).toBeVisible()
  return dialog
}

export async function expectAccuracyBreakdown(page: Page) {
  const table = getAccuracyDetails(page).getByRole('table', {
    name: 'Accuracy by market condition',
  })

  for (const market of MARKETS) {
    await expect(table).toContainText(market)
  }
}

/** The scorecard's own trend and comparison, scoped so the card's are ignored. */
export async function expectAccuracyDetailsCharts(
  dialog: Locator,
  horizon: string,
) {
  await expectAccuracyTrend(dialog)
  await expectAccuracyComparison(dialog, horizon)
}

export async function expectAccuracyDetailsFacts(dialog: Locator) {
  for (const label of ['Forecasts checked', 'Period', 'Last scored']) {
    await expect(dialog.getByText(label, { exact: true })).toBeVisible()
  }
  for (const metric of ['MAE', 'RMSE', 'MAPE']) {
    await expect(dialog).toContainText(metric)
  }
}

/** The dialog table's accuracy column, graded like the tiles. */
export async function expectBreakdownGraded(
  dialog: Locator,
  market: string,
  grade: MarketGrade,
) {
  const cell = dialog
    .getByRole('table', { name: 'Accuracy by market condition' })
    .getByRole('row', { name: new RegExp(market) })
    .getByRole('cell')
    .nth(1)

  await expect(cell).toHaveClass(GRADE_CLASSES[grade])
}

export async function expectAccuracyDetailsFocused(page: Page) {
  await expect(getAccuracyDetails(page)).toBeFocused()
}

export async function pressTabInDetails(page: Page) {
  await page.keyboard.press('Tab')
}

/** Tab never leaves the open dialog. */
export async function expectFocusInsideDetails(page: Page) {
  expect(
    await getAccuracyDetails(page).evaluate((dialog) =>
      dialog.contains(document.activeElement),
    ),
  ).toBe(true)
}

export async function pressEscape(page: Page) {
  await page.keyboard.press('Escape')
}

export async function expectFocusBackOnViewDetails(page: Page) {
  await expect(page.getByRole('button', { name: 'View details' })).toBeFocused()
}

export async function closeAccuracyDetails(page: Page) {
  await getAccuracyDetails(page)
    .getByRole('button', { name: 'Close', exact: true })
    .click()
}

export async function expectAccuracyDetailsClosed(page: Page) {
  await expect(page.getByRole('dialog')).toHaveCount(0)
}
