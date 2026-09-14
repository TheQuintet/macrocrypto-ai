import { cleanup } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, describe, expect, it } from 'vitest'
import { makeEconomicEvent } from '@/api/economicCalendar/economicCalendar.testHelpers'
import {
  PAST_EVENTS,
  expectCount,
  expectEmptyMessage,
  getEventButton,
  listedEventNames,
  manyPastEvents,
  queryPagination,
  renderEventHistory,
  searchHistory,
  setDateRange,
} from './EventHistory.testHelpers'

describe('EventHistory', () => {
  afterEach(() => {
    cleanup()
  })

  it('lists past events, most recent first', () => {
    renderEventHistory()

    expect(listedEventNames()).toEqual([
      'CPI release',
      'Non-farm payrolls',
      'FOMC minutes',
    ])
  })

  it('leaves out events that have not happened yet', () => {
    renderEventHistory([
      ...PAST_EVENTS,
      makeEconomicEvent({
        event_name: 'Future release',
        event_date: '2099-01-01T13:30:00.000Z',
      }),
    ])

    expect(listedEventNames()).not.toContain('Future release')
  })

  it('reports how many events are listed', () => {
    renderEventHistory()

    expectCount('3 events')
  })

  it('filters by search', async () => {
    const user = userEvent.setup()
    renderEventHistory()

    await searchHistory(user, 'payrolls')

    expect(listedEventNames()).toEqual(['Non-farm payrolls'])
  })

  it('filters by an inclusive date range', () => {
    renderEventHistory()

    setDateRange('2024-03-01', '2024-03-12')

    expect(listedEventNames()).toEqual(['CPI release', 'Non-farm payrolls'])
  })

  it('says when filters match nothing, distinct from having no history', async () => {
    const user = userEvent.setup()
    renderEventHistory()

    await searchHistory(user, 'nothing matches this')

    expectEmptyMessage('No past events match these filters.')
  })

  it('says when there is no history at all', () => {
    renderEventHistory([])

    expectEmptyMessage('No past events in the calendar yet.')
  })

  it('reports a clicked event to the caller', async () => {
    const user = userEvent.setup()
    const { onSelectEvent } = renderEventHistory()

    await user.click(getEventButton('CPI release'))

    expect(onSelectEvent).toHaveBeenCalledWith(
      expect.objectContaining({ event_name: 'CPI release' }),
    )
  })

  it('paginates once past a single page', () => {
    renderEventHistory(manyPastEvents())

    expect(listedEventNames()).toHaveLength(10)
    expect(queryPagination()).toBeInTheDocument()
  })

  it('does not paginate a short history', () => {
    renderEventHistory()

    expect(queryPagination()).not.toBeInTheDocument()
  })
})
