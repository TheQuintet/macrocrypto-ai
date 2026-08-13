import { expect, type Page } from '@playwright/test'

const CANDLE_COLORS = ['var(--positive)', 'var(--negative)']

export async function selectChartType(page: Page, label: 'Line' | 'Candles') {
  await page
    .getByRole('group', { name: 'Chart type' })
    .getByRole('button', { name: label, exact: true })
    .click()
}

export async function expectChartTypeSelected(page: Page, label: string) {
  await expect(
    page
      .getByRole('group', { name: 'Chart type' })
      .getByRole('button', { name: label, exact: true }),
  ).toHaveAttribute('aria-pressed', 'true')
}

/** Measure the drawn candles straight off the SVG. */
async function readCandles(page: Page) {
  return page.evaluate((colors) => {
    const surfaces = [...document.querySelectorAll('svg.recharts-surface')]
    const plot = surfaces[surfaces.length - 1]
    if (!plot) {
      return null
    }

    const isCandle = (value: string | null) =>
      value !== null && colors.includes(value)
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
  }, CANDLE_COLORS)
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

export async function expectLineRendered(page: Page) {
  await expect(
    page.locator('svg.recharts-surface .recharts-line-curve').first(),
  ).toBeVisible({ timeout: 15_000 })
}

export async function expectNoCandles(page: Page) {
  const candles = await readCandles(page)
  expect(candles?.count ?? 0).toBe(0)
}
