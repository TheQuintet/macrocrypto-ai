import { cleanup } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, describe, expect, it } from 'vitest'
import {
  closeDialog,
  expectDialogMentions,
  expectDialogShows,
  expectManageAlertsLink,
  expectNothingRendered,
  renderEventDetailsDialog,
} from './EventDetailsDialog.testHelpers'

describe('EventDetailsDialog', () => {
  afterEach(() => {
    cleanup()
  })

  it('renders nothing when no event is selected', () => {
    renderEventDetailsDialog({ event: null })

    expectNothingRendered()
  })

  it('shows the event with its date, zone, category, and impact', () => {
    renderEventDetailsDialog()

    expectDialogShows('FOMC rate decision')
    expectDialogMentions(/18 Mar 2026/)
    expectDialogMentions(/19:00/)
    expectDialogMentions(/UTC/)
    expectDialogShows('Fed')
    expectDialogShows('High impact')
    expectDialogShows('Federal Reserve policy decision.')
  })

  it('renders the time in the display timezone it is given', () => {
    renderEventDetailsDialog({ timeZone: 'America/New_York' })

    expectDialogMentions(/15:00/)
  })

  it('spells out that a subscribed event will alert the reader', () => {
    renderEventDetailsDialog({ subscribed: true })

    expectDialogShows('Alerts on')
    expectDialogMentions(/You will be alerted before this event\./)
  })

  it('spells out that an unsubscribed event will not', () => {
    renderEventDetailsDialog({ subscribed: false })

    expectDialogShows('No alerts')
    expectDialogMentions(/You will not be alerted before this event\./)
  })

  it('admits when the subscription lookup failed instead of guessing', () => {
    renderEventDetailsDialog({ subscribed: null })

    expectDialogShows('Alert status unavailable')
    expectDialogMentions(/subscriptions could not be loaded/)
  })

  it('points at the alerts page, where subscriptions are managed', () => {
    renderEventDetailsDialog()

    expectManageAlertsLink()
  })

  it('closes on the close button', async () => {
    const user = userEvent.setup()
    const { onClose } = renderEventDetailsDialog()

    await closeDialog(user)

    expect(onClose).toHaveBeenCalledTimes(1)
  })
})
