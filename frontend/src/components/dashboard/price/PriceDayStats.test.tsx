import { cleanup } from '@testing-library/react'
import { afterEach, describe, it } from 'vitest'
import {
  expectDayStat,
  renderPriceDayStats,
} from '@/components/dashboard/price/PriceDayStats.testHelpers'

describe('PriceDayStats', () => {
  afterEach(() => {
    cleanup()
  })

  it('shows the 24h high, low and volume', () => {
    renderPriceDayStats(64_993.5, 63_573.5, 24_180.42)

    expectDayStat('24h high', '$64,993.50')
    expectDayStat('24h low', '$63,573.50')
    expectDayStat('24h volume', '24,180.42 BTC')
  })

  it('placeholders values the service has not reported', () => {
    renderPriceDayStats(null, null, null)

    expectDayStat('24h high', '--')
    expectDayStat('24h low', '--')
    expectDayStat('24h volume', '--')
  })

  it('shows the values it has when only some are missing', () => {
    renderPriceDayStats(64_993.5, null, 24_180.42)

    expectDayStat('24h high', '$64,993.50')
    expectDayStat('24h low', '--')
    expectDayStat('24h volume', '24,180.42 BTC')
  })
})
