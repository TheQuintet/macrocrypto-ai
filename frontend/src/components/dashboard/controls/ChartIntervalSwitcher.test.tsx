import { cleanup, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, beforeEach, describe, expect, it } from 'vitest'
import {
  expectCandleInterval,
  expectIntervalDisabled,
  expectIntervalNotSelected,
  expectIntervalSelected,
  getIntervalGroup,
  renderChartIntervalSwitcher,
  selectChartInterval,
} from '@/components/dashboard/controls/ChartIntervalSwitcher.testHelpers'
import { resetPreferencesStore } from '@/stores/preferencesStore.testHelpers'
import { usePreferencesStore } from '@/stores/preferencesStore'

describe('ChartIntervalSwitcher', () => {
  beforeEach(() => {
    resetPreferencesStore()
  })

  afterEach(() => {
    cleanup()
    resetPreferencesStore()
  })

  it('opens on daily candles', () => {
    renderChartIntervalSwitcher()

    expectIntervalSelected('Daily')
    expectIntervalNotSelected('Weekly')
    expectCandleInterval('1d')
  })

  it('marks the chosen interval as selected and updates preferences', async () => {
    const user = userEvent.setup()
    renderChartIntervalSwitcher()

    await selectChartInterval(user, 'Weekly')

    expectIntervalSelected('Weekly')
    expectIntervalNotSelected('Daily')
    expectCandleInterval('1w')
  })

  it('offers only daily and weekly', () => {
    renderChartIntervalSwitcher()

    const group = getIntervalGroup()
    expect(within(group).getAllByRole('button')).toHaveLength(2)
    expect(within(group).getByRole('button', { name: 'Daily' })).toBeInTheDocument()
    expect(
      within(group).getByRole('button', { name: 'Weekly' }),
    ).toBeInTheDocument()
  })

  it('locks 1y and 5y to weekly candles', () => {
    usePreferencesStore.getState().setTimeRange('1y')
    renderChartIntervalSwitcher()

    expectIntervalSelected('Weekly')
    expectIntervalDisabled('Daily')
    expectCandleInterval('1w')
  })
})
