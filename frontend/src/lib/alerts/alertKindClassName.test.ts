import { describe, expect, it } from 'vitest'
import {
  alertKindButtonClassName,
  alertKindIconClassName,
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
  })

  it('fills the create button with the same kind color', () => {
    expect(alertKindButtonClassName('price')).toContain('bg-[var(--toast-price-bg)]')
    expect(alertKindButtonClassName('prediction')).toContain('bg-[var(--toast-forecast-bg)]')
    expect(alertKindButtonClassName('macro')).toContain('bg-[var(--toast-macro-bg)]')
  })

  it('pairs each fill with its readable text token', () => {
    expect(alertKindButtonClassName('price')).toContain('text-[var(--toast-price-text)]')
  })

  it('tints idle create-popup icons with the kind color', () => {
    expect(alertKindIconClassName('price', false)).toContain('--toast-price-bg')
    expect(alertKindIconClassName('macro', false)).toContain('--toast-macro-bg')
    expect(alertKindIconClassName('prediction', false)).toContain('--toast-forecast-bg')
  })

  it('fills the selected create-popup icon with the kind color', () => {
    expect(alertKindIconClassName('price', true)).toBe(alertKindButtonClassName('price'))
  })
})
