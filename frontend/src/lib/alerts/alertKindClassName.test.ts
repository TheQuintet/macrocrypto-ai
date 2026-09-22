import { describe, expect, it } from 'vitest'
import {
  alertKindDotClassName,
  alertKindTabClassName,
} from '@/lib/alerts/alertKindClassName'

describe('alertKindClassName', () => {
  it('uses the toast color tokens for each alert kind', () => {
    expect(alertKindTabClassName('price', true)).toContain('--toast-price-bg')
    expect(alertKindTabClassName('prediction', true)).toContain('--toast-forecast-bg')
    expect(alertKindTabClassName('macro', true)).toContain('--toast-macro-bg')
  })

  it('keeps kind color on idle tabs so the code is always visible', () => {
    expect(alertKindTabClassName('price', false)).toContain('--toast-price-bg')
    expect(alertKindTabClassName('price', false)).not.toContain('text-muted-foreground')
    expect(alertKindDotClassName('macro')).toContain('--toast-macro-bg')
  })
})
