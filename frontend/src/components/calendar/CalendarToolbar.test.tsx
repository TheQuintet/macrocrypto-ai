import { cleanup } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, describe, expect, it } from 'vitest'
import {
  clickPeriodButton,
  expectPeriodLabel,
  expectStepButtonsFor,
  expectViewSelected,
  getTimezoneSelect,
  renderCalendarToolbar,
  selectTimezoneMode,
  selectView,
} from './CalendarToolbar.testHelpers'

describe('CalendarToolbar', () => {
  afterEach(() => {
    cleanup()
  })

  it('shows the period and marks the active view', () => {
    renderCalendarToolbar()

    expectPeriodLabel('March 2026')
    expectViewSelected('Month', true)
    expectViewSelected('Week', false)
  })

  it('names the step buttons after the current view', () => {
    renderCalendarToolbar({ view: 'week' })

    expectStepButtonsFor('week')
  })

  it('steps the period', async () => {
    const user = userEvent.setup()
    const handlers = renderCalendarToolbar()

    await clickPeriodButton(user, 'Previous month')
    await clickPeriodButton(user, 'Next month')

    expect(handlers.onPrevious).toHaveBeenCalledTimes(1)
    expect(handlers.onNext).toHaveBeenCalledTimes(1)
  })

  it('reports a view change', async () => {
    const user = userEvent.setup()
    const handlers = renderCalendarToolbar()

    await selectView(user, 'Week')

    expect(handlers.onViewChange).toHaveBeenCalledWith('week')
  })

  it('offers the reader their own zone and UTC, and reports the switch', async () => {
    const user = userEvent.setup()
    const handlers = renderCalendarToolbar()

    expect(getTimezoneSelect()).toHaveValue('local')
    expect(getTimezoneSelect()).toHaveTextContent('Europe/Bucharest')

    await selectTimezoneMode(user, 'utc')

    expect(handlers.onTimezoneModeChange).toHaveBeenCalledWith('utc')
  })
})
