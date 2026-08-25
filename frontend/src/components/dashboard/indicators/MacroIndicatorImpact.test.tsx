import { cleanup } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, describe, expect, it } from 'vitest'
import {
  expectTooltipCopy,
  getImpactTrigger,
  openImpactTooltip,
  renderImpact,
} from './MacroIndicatorImpact.testHelpers'

describe('MacroIndicatorImpact', () => {
  afterEach(() => {
    cleanup()
  })

  it('colors a rising CPI print as negative for BTC', () => {
    renderImpact('cpi', 0.23)

    const trigger = getImpactTrigger()
    expect(trigger).toHaveTextContent('↑ +0.23%')
    expect(trigger).toHaveClass('text-negative')
    expect(trigger).toHaveAttribute(
      'aria-label',
      '+0.23%, Negative for BTC',
    )
  })

  it('explains why the print is positive or negative in a tooltip', async () => {
    const user = userEvent.setup()
    renderImpact('gdp', 1.91)

    await openImpactTooltip(user)

    expectTooltipCopy('Positive for BTC')
    expectTooltipCopy(/Stronger GDP is typically positive for BTC/)
  })
})
