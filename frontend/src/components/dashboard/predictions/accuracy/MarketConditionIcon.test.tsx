import { cleanup } from '@testing-library/react'
import { afterEach, describe, expect, it } from 'vitest'
import type { MarketCondition } from '@/types/predictionAccuracy'
import {
  expectNeutralDecorativeIcon,
  renderMarketIcon,
} from './MarketConditionIcon.testHelpers'

const CONDITIONS: MarketCondition[] = ['bull', 'bear', 'volatile', 'neutral']

describe('MarketConditionIcon', () => {
  afterEach(() => {
    cleanup()
  })

  it('marks every market in a neutral colour, leaving colour to the grade', () => {
    for (const condition of CONDITIONS) {
      expectNeutralDecorativeIcon(renderMarketIcon(condition))
      cleanup()
    }
  })

  it('gives each market its own shape', () => {
    const shapes = CONDITIONS.map(
      (condition) => renderMarketIcon(condition)?.innerHTML,
    )

    expect(new Set(shapes).size).toBe(CONDITIONS.length)
  })
})
