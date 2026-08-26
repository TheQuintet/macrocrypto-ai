import userEvent from '@testing-library/user-event'
import { cleanup } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'
import {
  expectFilterNotSelected,
  expectFilterSelectValue,
  expectFilterSelected,
  renderIndicatorHistoryFilter,
  selectIndicatorFilter,
  selectIndicatorFilterOption,
} from './IndicatorHistoryFilter.testHelpers'

describe('IndicatorHistoryFilter', () => {
  afterEach(() => {
    cleanup()
  })

  it('marks All as selected by default and reports the chosen series', async () => {
    const user = userEvent.setup()
    const onChange = vi.fn()
    renderIndicatorHistoryFilter('all', onChange)

    expectFilterSelected('All')
    expectFilterNotSelected('CPI')

    await selectIndicatorFilter(user, 'CPI')

    expect(onChange).toHaveBeenCalledWith('cpi')
  })

  it('exposes a combobox so the series can be chosen from a dropdown', async () => {
    const user = userEvent.setup()
    const onChange = vi.fn()
    renderIndicatorHistoryFilter('all', onChange)

    expectFilterSelectValue('all')

    await selectIndicatorFilterOption(user, 'federal_funds_rate')

    expect(onChange).toHaveBeenCalledWith('federal_funds_rate')
  })
})
