import { act } from '@testing-library/react'
import { beforeEach, describe, it } from 'vitest'
import {
  expectBadgeShows,
  renderTimeRangeBadge,
} from '@/components/timeRange/TimeRangeBadge.testHelpers'
import { usePreferencesStore } from '@/stores/preferencesStore'
import { resetPreferencesStore } from '@/stores/preferencesStore.testHelpers'

describe('TimeRangeBadge', () => {
  beforeEach(() => {
    resetPreferencesStore()
  })

  it('shows the current time range from preferences', () => {
    renderTimeRangeBadge()
    expectBadgeShows('7d')

    act(() => {
      usePreferencesStore.getState().setTimeRange('30d')
    })

    expectBadgeShows('30d')
  })
})
