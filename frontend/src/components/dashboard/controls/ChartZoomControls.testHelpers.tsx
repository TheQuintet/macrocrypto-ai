import { render, screen } from '@testing-library/react'
import { expect } from 'vitest'
import { ChartZoomControls } from '@/components/dashboard/controls/ChartZoomControls'
import { DEFAULT_CHART_POINT_WIDTH } from '@/components/dashboard/lib/chartZoom'

export function renderChartZoomControls() {
  return render(
    <ChartZoomControls
      pointWidth={DEFAULT_CHART_POINT_WIDTH}
      onZoomIn={() => undefined}
      onZoomOut={() => undefined}
    />,
  )
}

export function expectTouchFriendlyZoomButtons() {
  expect(screen.getByRole('button', { name: 'Zoom in' })).toHaveClass('size-11')
  expect(screen.getByRole('button', { name: 'Zoom out' })).toHaveClass(
    'size-11',
  )
}
