import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'
import {
  expectPeriodNotSelected,
  expectPeriodSelected,
  renderPeriodPicker,
  selectIndicatorPeriod,
} from './IndicatorPeriodPicker.testHelpers'

describe('IndicatorPeriodPicker', () => {
  it('marks the chosen period and reports the next selection', async () => {
    const user = userEvent.setup()
    const onChange = vi.fn()
    renderPeriodPicker('90d', onChange)

    expectPeriodSelected('90d')
    expectPeriodNotSelected('30d')

    await selectIndicatorPeriod(user, '1y')

    expect(onChange).toHaveBeenCalledWith('1y')
  })
})
