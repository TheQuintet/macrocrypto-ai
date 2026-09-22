import { cleanup, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, describe, expect, it } from 'vitest'
import {
  chooseEventType,
  chooseImpactLevel,
  expectEventAnnounces,
  expectEventGone,
  expectEventShown,
  expectCalendarGridGone,
  expectCalendarGridShown,
  expectListShown,
  expectSimulatedBadge,
  getPeriodHeading,
  openEventDetails,
  renderEconomicCalendar,
  stepToNextPeriod,
  switchToListLayout,
  switchToWeekView,
} from './EconomicCalendar.testHelpers'

describe('EconomicCalendar', () => {
  afterEach(() => {
    cleanup()
  })

  it('renders the simulated schedule and labels it as simulated', async () => {
    renderEconomicCalendar()

    await expectEventShown('FOMC rate decision')
    expectSimulatedBadge()
  })

  it('marks events the reader is subscribed to', async () => {
    renderEconomicCalendar()

    // The simulated subscriptions cover Fed at the medium floor and CPI at high.
    await expectEventAnnounces('FOMC rate decision', 'alerts on')
    await expectEventAnnounces('Initial jobless claims', 'no alerts')
  })

  it('filters by event type', async () => {
    const user = userEvent.setup()
    renderEconomicCalendar()
    await expectEventShown('CPI release')

    await chooseEventType(user, 'fed')

    await expectEventShown('FOMC rate decision')
    await expectEventGone('CPI release')
  })

  it('filters by impact level', async () => {
    const user = userEvent.setup()
    renderEconomicCalendar()
    await expectEventShown('Initial jobless claims')

    await chooseImpactLevel(user, 'high')

    await expectEventShown('CPI release')
    await expectEventGone('Initial jobless claims')
  })

  it('opens the details of a clicked event', async () => {
    const user = userEvent.setup()
    renderEconomicCalendar()

    await openEventDetails(user, 'FOMC rate decision')

    expect(
      screen.getByText('Federal Reserve policy decision and statement. The single largest scheduled source of BTC volatility.'),
    ).toBeInTheDocument()
    expect(
      screen.getByRole('link', { name: 'Manage alerts' }),
    ).toBeInTheDocument()
  })

  it('switches between month and week and steps through periods', async () => {
    const user = userEvent.setup()
    renderEconomicCalendar()
    await expectEventShown('FOMC rate decision')

    const monthLabel = getPeriodHeading()
    await switchToWeekView(user)
    const weekLabel = getPeriodHeading()
    expect(weekLabel).not.toBe(monthLabel)

    await stepToNextPeriod(user, 'week')
    expect(getPeriodHeading()).not.toBe(weekLabel)
  })

  it('switches the same period to a list', async () => {
    const user = userEvent.setup()
    renderEconomicCalendar()
    await expectEventShown('FOMC rate decision')
    expectCalendarGridShown()

    await switchToListLayout(user)

    await expectListShown('FOMC rate decision')
    expectCalendarGridGone()
  })

  it('keeps filters when the list is showing', async () => {
    const user = userEvent.setup()
    renderEconomicCalendar()
    await expectEventShown('CPI release')
    await switchToListLayout(user)
    await expectListShown('CPI release')

    await chooseEventType(user, 'fed')

    await expectListShown('FOMC rate decision')
    expect(screen.queryByRole('button', { name: 'CPI release' })).not.toBeInTheDocument()
  })
})
