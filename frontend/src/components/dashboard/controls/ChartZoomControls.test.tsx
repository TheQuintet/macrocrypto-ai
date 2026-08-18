import { describe, it } from 'vitest'
import {
  expectTouchFriendlyZoomButtons,
  renderChartZoomControls,
} from '@/components/dashboard/controls/ChartZoomControls.testHelpers'

describe('ChartZoomControls', () => {
  it('uses larger touch targets on small screens', () => {
    renderChartZoomControls()
    expectTouchFriendlyZoomButtons()
  })
})
