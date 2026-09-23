import { cleanup } from '@testing-library/react'
import { afterEach, describe, it } from 'vitest'
import {
  expectConfidenceScaleKey,
  renderRegimeConfidenceScale,
} from '@/components/dashboard/regime/RegimeConfidenceScale.testHelpers'

describe('RegimeConfidenceScale', () => {
  afterEach(() => {
    cleanup()
  })

  it('shows low, moderate, and high with their ranges', () => {
    renderRegimeConfidenceScale()
    expectConfidenceScaleKey()
  })
})
