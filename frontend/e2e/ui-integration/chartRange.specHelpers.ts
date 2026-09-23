import { expect, type Page } from '@playwright/test'

const CANDLE_COLORS = ['var(--positive)', 'var(--negative)']

type PlotProbe = {
  candles: number
  medianCandleWidth: number | null
}

/**
 * Read the candles straight off the SVG.
 *
 * Candle count is the direct evidence for #510: with the range fitted, every
 * bucket in the range is drawn, so a wider range draws more of them. The old
 * behaviour drew roughly one screen's worth whatever the range was.
 */
export async function probePlot(page: Page): Promise<PlotProbe> {
  return page.evaluate((colors) => {
    const surfaces = [...document.querySelectorAll('svg.recharts-surface')]
    const bodies = surfaces.flatMap((surface) =>
      [...surface.querySelectorAll('rect')].filter((rect) =>
        colors.includes(rect.getAttribute('fill') ?? ''),
      ),
    )
    const widths = bodies
      .map((rect) => Number(rect.getAttribute('width')))
      .filter((width) => Number.isFinite(width))
      .sort((a, b) => a - b)

    return {
      candles: bodies.length,
      medianCandleWidth: widths.length
        ? widths[Math.floor(widths.length / 2)]
        : null,
    }
  }, CANDLE_COLORS)
}

export async function countCandles(page: Page) {
  return (await probePlot(page)).candles
}

/**
 * Wait for the plot to settle on a given candle count.
 *
 * Selecting a range refetches, and the previous range's candles stay on
 * screen until the new ones arrive — so "wait for any candles" would measure
 * the old range.
 */
export async function waitForCandleCount(page: Page, expected: number) {
  await expect
    .poll(async () => countCandles(page), { timeout: 20_000 })
    .toBe(expected)
}

export async function waitForCandlesToChangeFrom(page: Page, previous: number) {
  await expect
    .poll(async () => countCandles(page), { timeout: 20_000 })
    .not.toBe(previous)

  return countCandles(page)
}

export async function waitForAnyCandles(page: Page) {
  await expect
    .poll(async () => countCandles(page), { timeout: 20_000 })
    .toBeGreaterThan(0)
}

export function zoomGroup(page: Page) {
  return page.getByRole('group', { name: 'Chart zoom' })
}

export function zoomInButton(page: Page) {
  return zoomGroup(page).getByRole('button', { name: 'Zoom in' })
}

export function zoomOutButton(page: Page) {
  return zoomGroup(page).getByRole('button', { name: 'Zoom out' })
}

export async function zoomIn(page: Page, times = 1) {
  for (let index = 0; index < times; index += 1) {
    await zoomInButton(page).click()
  }
}

export function visibleRangeLine(page: Page) {
  return page.getByText(/^Showing/)
}

export async function readVisibleRangeText(page: Page) {
  const line = visibleRangeLine(page)
  await expect(line).toBeVisible({ timeout: 20_000 })

  return (await line.textContent()) ?? ''
}

/**
 * Days between the two ends of the reported window.
 *
 * The boundaries carry a year, so this stays correct across a range that
 * spans New Year — the case that read as "Sep 15 → Sep 15" before.
 */
export async function readVisibleSpanDays(page: Page) {
  const text = await readVisibleRangeText(page)
  const [from, to] = text
    .replace(/^Showing\s*/, '')
    .split('→')
    .map((part) => part.split('·')[0].trim())

  const fromMs = Date.parse(from)
  const toMs = Date.parse(to)

  expect(Number.isNaN(fromMs), `unreadable start: "${from}"`).toBe(false)
  expect(Number.isNaN(toMs), `unreadable end: "${to}"`).toBe(false)

  return Math.round((toMs - fromMs) / 86_400_000)
}
