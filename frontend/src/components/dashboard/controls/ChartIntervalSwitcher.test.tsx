import { cleanup } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, describe, expect, it, vi } from 'vitest'
import {
  expectIntervalSelected,
  expectTouchFriendlyIntervalButtons,
  renderChartIntervalSwitcher,
  selectChartInterval,
} from '@/components/dashboard/controls/ChartIntervalSwitcher.testHelpers'

describe('ChartIntervalSwitcher', () => {
  afterEach(() => {
    cleanup()
  })

  it('marks the chosen interval as selected', async () => {
    const user = userEvent.setup()
    const onChange = vi.fn()
    renderChartIntervalSwitcher('1h', onChange)
    expectIntervalSelected('1h')

    await selectChartInterval(user, '1d')

    expect(onChange).toHaveBeenCalledWith('1d')
  })

  it('uses full-width touch-friendly targets on small screens', () => {
    renderChartIntervalSwitcher()
    expectTouchFriendlyIntervalButtons()
  })
})
