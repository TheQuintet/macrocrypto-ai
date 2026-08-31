import { cleanup } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, describe, expect, it } from 'vitest'
import {
  expectAlertStatusFilterSelected,
  renderAlertStatusFilter,
  selectAlertStatusFilter,
} from './AlertStatusFilter.testHelpers'

afterEach(() => {
  cleanup()
})

describe('AlertStatusFilter', () => {
  it('marks All as selected by default', () => {
    renderAlertStatusFilter()

    expectAlertStatusFilterSelected('All')
  })

  it('notifies when Active is selected', async () => {
    const user = userEvent.setup()
    const { onChange } = renderAlertStatusFilter()

    await selectAlertStatusFilter(user, 'Active')

    expect(onChange).toHaveBeenCalledWith('active')
  })

  it('notifies when Inactive is selected', async () => {
    const user = userEvent.setup()
    const { onChange } = renderAlertStatusFilter()

    await selectAlertStatusFilter(user, 'Inactive')

    expect(onChange).toHaveBeenCalledWith('inactive')
  })
})
