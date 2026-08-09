import { act } from '@testing-library/react'
import { beforeEach, describe, it } from 'vitest'
import {
  expectBadgeShows,
  renderTimeRangeBadge,
} from '@/components/time-range-badge.test-helpers'
import { usePreferencesStore } from '@/stores/preferences-store'
import { resetPreferencesStore } from '@/stores/preferences-store.test-helpers'

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
