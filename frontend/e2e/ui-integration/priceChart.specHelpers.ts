import { expect, type Page } from '@playwright/test'

const CANDLE_COLORS = ['var(--positive)', 'var(--negative)']

/**
 * The dashboard's price plot, not the forecast card above it: that chart
 * draws the same candles, so a page-wide search would land on it first.
 */
const PRICE_PLOT_SURFACES =
  'svg.recharts-surface:not([aria-label$="price forecast"] *)'

/** Measure the drawn candles straight off the SVG. */
async function readCandles(page: Page) {
  return page.evaluate(({ colors, plotSelector }) => {
    const surfaces = [...document.querySelectorAll(plotSelector)]
    const isCandle = (value: string | null) =>
      value !== null && colors.includes(value)
    const plot =
      surfaces.find((surface) => {
        const wicks = [...surface.querySelectorAll('line')].some((line) =>
          isCandle(line.getAttribute('stroke')),
        )
        const bodies = [...surface.querySelectorAll('rect')].some((rect) =>
          isCandle(rect.getAttribute('fill')),
        )
        return wicks || bodies
      }) ?? surfaces[surfaces.length - 1]
    if (!plot) {
      return null
    }
    const wicks = [...plot.querySelectorAll('line')].filter((line) =>
      isCandle(line.getAttribute('stroke')),
    )
    const bodies = [...plot.querySelectorAll('rect')].filter((rect) =>
      isCandle(rect.getAttribute('fill')),
    )

    const num = (el: Element, attr: string) => Number(el.getAttribute(attr))

    return {
      plotHeight: Number(plot.getAttribute('height')),
      count: bodies.length,
      wickSpans: wicks.map((l) => num(l, 'y2') - num(l, 'y1')),
      bodyHeights: bodies.map((r) => num(r, 'height')),
      contained: bodies.every((rect, index) => {
        const wick = wicks[index]
        if (!wick) return true
        return (
          num(rect, 'y') >= num(wick, 'y1') - 0.5 &&
          num(rect, 'y') + num(rect, 'height') <= num(wick, 'y2') + 1.5
        )
      }),
      centered: bodies.every((rect, index) => {
        const wick = wicks[index]
        if (!wick) return true
        return (
          Math.abs(num(rect, 'x') + num(rect, 'width') / 2 - num(wick, 'x1')) <
          0.6
        )
      }),
    }
  }, { colors: CANDLE_COLORS, plotSelector: PRICE_PLOT_SURFACES })
}

export async function expectCandlesRendered(page: Page) {
  await expect
    .poll(async () => (await readCandles(page))?.count ?? 0, {
      timeout: 15_000,
    })
    .toBeGreaterThan(0)
}

/**
 * Candles must use a real share of the plot. Guards the regression where the
 * Y axis scaled to the whole series and squashed every candle to a sliver.
 */
export async function expectCandlesFillPlot(page: Page) {
  const candles = await readCandles(page)
  expect(candles).not.toBeNull()

  const tallestWick = Math.max(...candles!.wickSpans)
  expect(tallestWick / candles!.plotHeight).toBeGreaterThan(0.08)

  const tallestBody = Math.max(...candles!.bodyHeights)
  expect(tallestBody).toBeGreaterThan(2)
}

export async function expectCandleShapesWellFormed(page: Page) {
  const candles = await readCandles(page)

  expect(candles?.contained).toBe(true)
  expect(candles?.centered).toBe(true)
}

/**
 * Hover a candle that is actually on screen.
 *
 * Uses the candle's own client rect rather than SVG coordinates: the plot
 * strip is translated and clipped for panning, so SVG-space maths can land
 * outside the visible area.
 */
export async function hoverMiddleCandle(page: Page) {
  const point = await page.evaluate(({ colors, plotSelector }) => {
    const surface = [...document.querySelectorAll(plotSelector)].find(
      (plot) =>
        [...plot.querySelectorAll('line')].some((line) =>
          colors.includes(line.getAttribute('stroke') ?? ''),
        ),
    )
    if (!surface) {
      return null
    }

    // The forecast card sits above the price chart, so on a short viewport
    // the plot starts below the fold.
    surface.scrollIntoView({ block: 'center' })

    const visible = [...surface.querySelectorAll('line')]
      .filter((line) => colors.includes(line.getAttribute('stroke') ?? ''))
      .map((line) => line.getBoundingClientRect())
      .filter(
        (rect) =>
          rect.left >= 0 &&
          rect.right <= window.innerWidth &&
          rect.top >= 0 &&
          rect.bottom <= window.innerHeight,
      )

    if (visible.length === 0) {
      return null
    }

    const rect = visible[Math.floor(visible.length / 2)]
    return { x: rect.left + rect.width / 2, y: rect.top + rect.height / 2 }
  }, { colors: CANDLE_COLORS, plotSelector: PRICE_PLOT_SURFACES })

  expect(point, 'no candle visible to hover').not.toBeNull()
  await page.mouse.move(point!.x, point!.y)
}

export async function movePointerOffChart(page: Page) {
  await page.mouse.move(4, 4)
}

function hoverLine(page: Page) {
  return page.locator('[data-slot="candle-hover-line"]')
}

/** A vertical marker on the hovered candle, spanning the plot. */
export async function expectCandleHoverLine(page: Page) {
  await expect(hoverLine(page)).toBeAttached({ timeout: 10_000 })

  const geometry = await page.evaluate(({ colors, plotSelector }) => {
    const surface = [...document.querySelectorAll(plotSelector)].find(
      (plot) =>
        [...plot.querySelectorAll('line')].some((line) =>
          colors.includes(line.getAttribute('stroke') ?? ''),
        ),
    )
    const line = surface?.querySelector('[data-slot="candle-hover-line"]')
    if (!surface || !line) {
      return null
    }

    const num = (el: Element, attr: string) => Number(el.getAttribute(attr))
    const wicks = [...surface.querySelectorAll('line')].filter((l) =>
      colors.includes(l.getAttribute('stroke') ?? ''),
    )
    const grid = [
      ...surface.querySelectorAll('.recharts-cartesian-grid-horizontal line'),
    ].map((l) => num(l, 'y1'))

    return {
      isVertical: num(line, 'x1') === num(line, 'x2'),
      offFromNearestCandle: Math.min(
        ...wicks.map((w) => Math.abs(num(w, 'x1') - num(line, 'x1'))),
      ),
      spanTop: num(line, 'y1'),
      spanBottom: num(line, 'y2'),
      plotTop: Math.min(...grid),
      plotBottom: Math.max(...grid),
    }
  }, { colors: CANDLE_COLORS, plotSelector: PRICE_PLOT_SURFACES })

  expect(geometry).not.toBeNull()
  expect(geometry!.isVertical).toBe(true)
  // Lands on a candle, not between two of them.
  expect(geometry!.offFromNearestCandle).toBeLessThan(1)
  // Covers the plot so the candle is traceable top to bottom.
  expect(Math.abs(geometry!.spanTop - geometry!.plotTop)).toBeLessThan(2)
  expect(Math.abs(geometry!.spanBottom - geometry!.plotBottom)).toBeLessThan(2)
}

export async function expectNoCandleHoverLine(page: Page) {
  await expect(hoverLine(page)).toHaveCount(0, { timeout: 10_000 })
}

/** The candle tooltip breaks the bucket down into O/H/L/C. */
export async function expectOhlcTooltip(page: Page) {
  const tooltip = page.getByRole('tooltip')
  await expect(tooltip).toBeVisible({ timeout: 10_000 })
  for (const label of ['Open', 'High', 'Low', 'Close']) {
    await expect(tooltip).toContainText(label)
  }
}

export async function expectCandleReadoutHint(page: Page) {
  await expect(page.getByRole('region', { name: 'Selected candle' })).toContainText(
    /tap a candle/i,
  )
}

export async function expectCandleReadout(page: Page) {
  const readout = page.getByRole('region', { name: 'Selected candle' })
  await expect(readout).toBeVisible()
  for (const label of ['Open', 'High', 'Low', 'Close']) {
    await expect(readout).toContainText(label)
  }
}

function candleIntervalGroup(page: Page) {
  return page.getByRole('group', { name: 'Chart interval' })
}

export async function selectCandleInterval(
  page: Page,
  label: 'Daily' | 'Weekly',
) {
  await candleIntervalGroup(page)
    .getByRole('button', { name: label, exact: true })
    .click()
}

export async function expectCandleIntervalSelected(
  page: Page,
  label: 'Daily' | 'Weekly',
) {
  await expect(
    candleIntervalGroup(page).getByRole('button', { name: label, exact: true }),
  ).toHaveAttribute('aria-pressed', 'true')
}
