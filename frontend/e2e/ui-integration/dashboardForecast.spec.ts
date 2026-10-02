import { test } from '@playwright/test'
import { goToRoute } from './routing.specHelpers'
import {
  DESKTOP_VIEWPORT,
  MOBILE_VIEWPORT,
  TABLET_VIEWPORT,
  expectNoHorizontalScroll,
} from './priceDisplay.specHelpers'
import {
  expectActualThenForecast,
  expectFiguresBesideChart,
  expectForecastCardRendered,
  expectForecastFigures,
  expectForecastTooltip,
  expectLinkTappable,
  expectOnForecastsPage,
  expectStackedWithinViewport,
  openForecasts,
  tapForecast,
} from './dashboardForecast.specHelpers'

test.describe('dashboard forecast card UI integration', () => {
  test('shows the 24h forecast after the actual price, with its band', async ({
    page,
  }) => {
    await goToRoute(page, 'dashboard')

    await expectForecastCardRendered(page)
    await expectActualThenForecast(page)
  })

  test('shows the predicted price, change, range and coverage alongside', async ({
    page,
  }) => {
    await goToRoute(page, 'dashboard')
    await expectForecastCardRendered(page)

    await expectForecastFigures(page)
  })

  test('opens the Forecasts page from the card', async ({ page }) => {
    await goToRoute(page, 'dashboard')
    await expectForecastCardRendered(page)

    await openForecasts(page)

    await expectOnForecastsPage(page)
  })

  test('puts the figures beside the chart on desktop', async ({ page }) => {
    await page.setViewportSize(DESKTOP_VIEWPORT)
    await goToRoute(page, 'dashboard')
    await expectForecastCardRendered(page)

    await expectFiguresBesideChart(page)
  })
})

test.describe('dashboard forecast card responsive UI integration', () => {
  for (const [name, viewport] of [
    ['tablet', TABLET_VIEWPORT],
    ['mobile', MOBILE_VIEWPORT],
  ] as const) {
    test(`stacks the figures under the chart on ${name} without horizontal scrolling`, async ({
      page,
    }) => {
      await page.setViewportSize(viewport)
      await goToRoute(page, 'dashboard')
      await expectForecastCardRendered(page)

      await expectStackedWithinViewport(page)
      await expectNoHorizontalScroll(page)
    })
  }

  test('keeps the link tappable on mobile', async ({ page }) => {
    await page.setViewportSize(MOBILE_VIEWPORT)
    await goToRoute(page, 'dashboard')
    await expectForecastCardRendered(page)

    await expectLinkTappable(page)
    await openForecasts(page)

    await expectOnForecastsPage(page)
  })
})

/** A real touch-capable context; `setViewportSize` alone leaves touch off. */
test.describe('dashboard forecast card touch UI integration', () => {
  test.use({ viewport: MOBILE_VIEWPORT, hasTouch: true })

  test('reaches the forecast tooltip by touch', async ({ page }) => {
    await goToRoute(page, 'dashboard')
    await expectForecastCardRendered(page)

    await tapForecast(page)

    await expectForecastTooltip(page)
  })
})
