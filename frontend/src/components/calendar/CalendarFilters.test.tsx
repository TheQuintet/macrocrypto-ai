import { cleanup } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, describe, expect, it } from 'vitest'
import {
  expectFilterValues,
  getEventTypeFilter,
  renderCalendarFilters,
  selectEventType,
  selectImpactLevel,
} from './CalendarFilters.testHelpers'

describe('CalendarFilters', () => {
  afterEach(() => {
    cleanup()
  })

  it('starts on the unfiltered value for both filters', () => {
    renderCalendarFilters()

    expectFilterValues('all', 'all')
  })

  it('offers every category the backend accepts', () => {
    renderCalendarFilters()

    expect(
      [...getEventTypeFilter().querySelectorAll('option')].map(
        (option) => option.value,
      ),
    ).toEqual(['all', 'fed', 'cpi', 'employment', 'gdp'])
  })

  it('reports the chosen event type', async () => {
    const user = userEvent.setup()
    const handlers = renderCalendarFilters()

    await selectEventType(user, 'fed')

    expect(handlers.onEventTypeChange).toHaveBeenCalledWith('fed')
  })

  it('reports the chosen impact level', async () => {
    const user = userEvent.setup()
    const handlers = renderCalendarFilters()

    await selectImpactLevel(user, 'high')

    expect(handlers.onImpactLevelChange).toHaveBeenCalledWith('high')
  })
})
