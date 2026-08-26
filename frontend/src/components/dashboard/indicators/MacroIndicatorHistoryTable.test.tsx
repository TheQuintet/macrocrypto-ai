import { cleanup } from '@testing-library/react'
import { afterEach, describe, it } from 'vitest'
import {
  expectRowUsesSeriesColor,
  renderHistoryTable,
} from './MacroIndicatorHistoryTable.testHelpers'

describe('MacroIndicatorHistoryTable', () => {
  afterEach(() => {
    cleanup()
  })

  it('colors each row with the matching chart series color', () => {
    renderHistoryTable()

    expectRowUsesSeriesColor('cpi')
    expectRowUsesSeriesColor('federal_funds_rate')
    expectRowUsesSeriesColor('gdp')
  })
})
