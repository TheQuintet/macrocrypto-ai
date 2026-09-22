import { cleanup } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, describe, expect, it } from 'vitest'
import {
  expectLayoutTabSelected,
  renderCalendarLayoutTabs,
  selectLayoutTab,
} from './CalendarLayoutTabs.testHelpers'

describe('CalendarLayoutTabs', () => {
  afterEach(() => {
    cleanup()
  })

  it('marks Calendar as the open tab', () => {
    renderCalendarLayoutTabs()

    expectLayoutTabSelected('Calendar', true)
    expectLayoutTabSelected('List', false)
  })

  it('reports a switch to the list', async () => {
    const user = userEvent.setup()
    const { onChange } = renderCalendarLayoutTabs()

    await selectLayoutTab(user, 'List')

    expect(onChange).toHaveBeenCalledWith('list')
  })
})
