import { test } from '@playwright/test'
import { goToRoute } from './routing.specHelpers'
import {
  DESKTOP_VIEWPORT,
  MOBILE_VIEWPORT,
  expectNoHorizontalScroll,
} from './priceDisplay.specHelpers'
import {
  clickFirstSegment,
  closeDialog,
  expectBandWidensWithoutBreakingLayout,
  expectCurrentRegimeBadged,
  expectCurrentRegimeHighlighted,
  expectNarrowTableDropsDetailColumns,
  expectPerformanceMetrics,
  expectPerformanceRows,
  expectRegimeCardClassified,
  expectRegimeCardNamesARegime,
  expectRegimeDetailsDialog,
  expectSegmentTooltip,
  expectSimulatedBadges,
  expectTimelineSegments,
  expectWideTableShowsDetailColumns,
  expectZoomLevel,
  hoverFirstSegment,
  zoomInButton,
  zoomOutButton,
} from './regimes.specHelpers'

test.describe('macro regime UI integration', () => {
  test('dashboard names the current regime with a confidence meter', async ({
    page,
  }) => {
    await goToRoute(page, 'dashboard')

    await expectRegimeCardNamesARegime(page)
    await expectRegimeCardClassified(page)
  })

  test('performance page draws the regime band and highlights the current one', async ({
    page,
  }) => {
    await goToRoute(page, 'regimePerformance')

    await expectTimelineSegments(page, 2)
    await expectCurrentRegimeHighlighted(page)
  })

  test('hovering a regime shows its summary', async ({ page }) => {
    await goToRoute(page, 'regimePerformance')

    await expectTimelineSegments(page, 1)
    await hoverFirstSegment(page)
    await expectSegmentTooltip(page)
  })

  test('clicking a regime opens its details and Escape closes them', async ({
    page,
  }) => {
    await goToRoute(page, 'regimePerformance')

    await expectTimelineSegments(page, 1)
    await clickFirstSegment(page)
    await expectRegimeDetailsDialog(page)
    await closeDialog(page)
  })

  test('zooming widens the band without widening the page', async ({
    page,
  }) => {
    await goToRoute(page, 'regimePerformance')

    await expectTimelineSegments(page, 2)
    await expectZoomLevel(page, '1x')
    await expectBandWidensWithoutBreakingLayout(page)
    await expectNoHorizontalScroll(page)

    await zoomOutButton(page).click()
    await expectZoomLevel(page, '1x')
  })

  test('zoom stops at each end of its range', async ({ page }) => {
    await goToRoute(page, 'regimePerformance')

    await expectTimelineSegments(page, 2)
    await test.expect(zoomOutButton(page)).toBeDisabled()

    for (const level of ['2x', '4x', '8x']) {
      await zoomInButton(page).click()
      await expectZoomLevel(page, level)
    }

    await test.expect(zoomInButton(page)).toBeDisabled()
  })

  test('performance table shows every metric on a wide screen', async ({
    page,
  }) => {
    await page.setViewportSize(DESKTOP_VIEWPORT)
    await goToRoute(page, 'regimePerformance')

    await expectPerformanceMetrics(page)
    await expectPerformanceRows(page, 2)
    await expectWideTableShowsDetailColumns(page)
    await expectCurrentRegimeBadged(page)
  })

  test('regime views own up to running on simulated data', async ({ page }) => {
    await goToRoute(page, 'regimePerformance')
    await expectSimulatedBadges(page)
  })

  test('regime views fit a phone without sideways scroll', async ({ page }) => {
    await page.setViewportSize(MOBILE_VIEWPORT)
    await goToRoute(page, 'regimePerformance')

    await expectTimelineSegments(page, 2)
    await expectPerformanceRows(page, 2)
    await expectNarrowTableDropsDetailColumns(page)
    await expectNoHorizontalScroll(page)
  })

  test('regime card fits a phone without sideways scroll', async ({ page }) => {
    await page.setViewportSize(MOBILE_VIEWPORT)
    await goToRoute(page, 'dashboard')

    await expectRegimeCardClassified(page)
    await expectNoHorizontalScroll(page)
  })
})
