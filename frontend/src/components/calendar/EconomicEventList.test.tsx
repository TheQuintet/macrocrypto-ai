import { cleanup, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, describe, expect, it } from 'vitest'
import {
  expectEmptyPeriod,
  listedEventNames,
  openListedEvent,
  renderEconomicEventList,
} from './EconomicEventList.testHelpers'

describe('EconomicEventList', () => {
  afterEach(() => {
    cleanup()
  })

  it('lists the events in the current period', () => {
    renderEconomicEventList()

    expect(listedEventNames()).toEqual([
      'CPI release',
      'FOMC rate decision',
    ])
    expect(
      screen.getByLabelText('Economic calendar list, March 2026'),
    ).toBeInTheDocument()
  })

  it('opens an event from its name', async () => {
    const user = userEvent.setup()
    const { onSelectEvent } = renderEconomicEventList()

    await openListedEvent(user, 'FOMC rate decision')

    expect(onSelectEvent).toHaveBeenCalledWith(
      expect.objectContaining({ event_name: 'FOMC rate decision' }),
    )
  })

  it('says when the period is empty', () => {
    renderEconomicEventList({ events: [], periodLabel: 'March 2026' })

    expectEmptyPeriod('March 2026')
  })

  it('marks events the reader is subscribed to', () => {
    renderEconomicEventList({
      isSubscribed: (event) => event.event_type === 'fed',
    })

    expect(screen.getByText('Alerts on')).toBeInTheDocument()
    expect(screen.getByText('No alerts')).toBeInTheDocument()
  })
})
