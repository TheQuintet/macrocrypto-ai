import { cleanup } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { makeEconomicEvent } from '@/api/economicCalendar/economicCalendar.testHelpers'
import {
  clickEventChip,
  expectChipAnnounces,
  expectDayCellCount,
  expectDayCellRendered,
  expectWeekdayHeadings,
  getEventChip,
  renderCalendarGrid,
} from './CalendarGrid.testHelpers'

const fomc = makeEconomicEvent({
  event_name: 'FOMC rate decision',
  event_type: 'fed',
  impact_level: 'high',
  event_date: '2026-03-18T19:00:00.000Z',
})

describe('CalendarGrid', () => {
  afterEach(() => {
    cleanup()
  })

  it('lays March 2026 out as five Sunday-start weeks', () => {
    renderCalendarGrid()

    expectWeekdayHeadings()
    expectDayCellCount(35)
    expectDayCellRendered('Sun 1 Mar')
  })

  it('places an event on its day with the release time', () => {
    renderCalendarGrid({ events: [fomc] })

    expectChipAnnounces('FOMC rate decision', '19:00')
    expectChipAnnounces('FOMC rate decision', 'High impact')
  })

  it('announces whether the event will alert the reader', () => {
    renderCalendarGrid({ events: [fomc], isSubscribed: () => true })
    expectChipAnnounces('FOMC rate decision', 'alerts on')

    cleanup()

    renderCalendarGrid({ events: [fomc], isSubscribed: () => false })
    expectChipAnnounces('FOMC rate decision', 'no alerts')
  })

  it('says the status is unavailable rather than claiming no alerts', () => {
    renderCalendarGrid({ events: [fomc], isSubscribed: () => null })

    expectChipAnnounces('FOMC rate decision', 'alert status unavailable')
  })

  it('reports the clicked event to the caller', async () => {
    const user = userEvent.setup()
    const onSelectEvent = vi.fn()
    renderCalendarGrid({ events: [fomc], onSelectEvent })

    await clickEventChip(user, 'FOMC rate decision')

    expect(onSelectEvent).toHaveBeenCalledWith(fomc)
  })

  it('renders each event in the day it belongs to', () => {
    const cpi = makeEconomicEvent({
      event_name: 'CPI release',
      event_date: '2026-03-12T13:30:00.000Z',
    })
    renderCalendarGrid({ events: [fomc, cpi] })

    expect(getEventChip('CPI release')).toBeInTheDocument()
    expect(getEventChip('FOMC rate decision')).toBeInTheDocument()
  })
})
