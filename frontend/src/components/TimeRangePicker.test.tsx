import userEvent from '@testing-library/user-event'
import { beforeEach, describe, it } from 'vitest'
import {
  expectRangeNotSelected,
  expectRangeSelected,
  renderTimeRangePicker,
  selectTimeRange,
} from '@/components/time-range-picker.test-helpers'
import { resetPreferencesStore } from '@/stores/preferences-store.test-helpers'

describe('TimeRangePicker', () => {
  beforeEach(() => {
    resetPreferencesStore()
  })

  it('marks the chosen range as selected and updates preferences', async () => {
    const user = userEvent.setup()
    renderTimeRangePicker()
    expectRangeSelected('7d')

    await selectTimeRange(user, '30d')

    expectRangeSelected('30d')
    expectRangeNotSelected('7d')
  })
})
