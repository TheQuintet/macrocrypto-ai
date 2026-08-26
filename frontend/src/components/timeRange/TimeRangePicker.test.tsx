import userEvent from '@testing-library/user-event'
import { cleanup, screen, within } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it } from 'vitest'
import {
  expectRangeNotSelected,
  expectRangeSelected,
  renderTimeRangePicker,
  selectTimeRange,
} from '@/components/timeRange/TimeRangePicker.testHelpers'
import { resetPreferencesStore } from '@/stores/preferencesStore.testHelpers'

describe('TimeRangePicker', () => {
  beforeEach(() => {
    resetPreferencesStore()
  })

  afterEach(() => {
    cleanup()
    resetPreferencesStore()
  })

  it('marks the chosen range as selected and updates preferences', async () => {
    const user = userEvent.setup()
    renderTimeRangePicker()
    expectRangeSelected('30d')

    await selectTimeRange(user, '90d')

    expectRangeSelected('90d')
    expectRangeNotSelected('30d')
  })

  it('offers only 30d, 90d, 1y, and 5y', () => {
    renderTimeRangePicker()

    const picker = screen.getByRole('group', { name: 'Time range' })
    expect(within(picker).getAllByRole('button')).toHaveLength(4)
    expect(within(picker).getByRole('button', { name: '30d' })).toBeInTheDocument()
    expect(within(picker).getByRole('button', { name: '90d' })).toBeInTheDocument()
    expect(within(picker).getByRole('button', { name: '1y' })).toBeInTheDocument()
    expect(within(picker).getByRole('button', { name: '5y' })).toBeInTheDocument()
    expect(within(picker).queryByRole('button', { name: '24h' })).not.toBeInTheDocument()
    expect(within(picker).queryByRole('button', { name: '7d' })).not.toBeInTheDocument()
    expect(within(picker).queryByRole('button', { name: '6m' })).not.toBeInTheDocument()
  })
})
