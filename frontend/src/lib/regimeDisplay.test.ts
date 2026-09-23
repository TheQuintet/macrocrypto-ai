import { describe, expect, it } from 'vitest'
import {
  HIGH_CONFIDENCE_MIN,
  MODERATE_CONFIDENCE_MIN,
  clampConfidence,
  confidenceDisplay,
  formatConfidence,
  formatConfidenceBand,
  formatConfidenceBandRange,
  formatRegimeIdentifiedAt,
  regimeDisplay,
  toRegimeVisualIndicator,
} from '@/lib/regimeDisplay'

describe('regimeDisplay', () => {
  it('labels and explains every regime class the service can store', () => {
    const classes = [
      'high_inflation',
      'low_inflation',
      'rising_rates',
      'falling_rates',
      'recession',
      'growth',
    ] as const

    for (const regimeType of classes) {
      const display = regimeDisplay(regimeType, 'bull')

      expect(display.label).not.toMatch(/_/)
      expect(display.explanation.length).toBeGreaterThan(20)
    }
  })

  it('takes the stance from the service, not from the regime class', () => {
    // `growth` reads bullish in the service's own mapping, but the stance
    // shown must follow whatever the payload says — one source of truth.
    expect(regimeDisplay('growth', 'bear').stance).toBe('bearish')
    expect(regimeDisplay('high_inflation', 'bull').stance).toBe('bullish')
  })

  it('colours bullish green, bearish red, and neutral amber', () => {
    expect(regimeDisplay('growth', 'bull').toneClass).toBe('text-positive')
    expect(regimeDisplay('high_inflation', 'bear').toneClass).toBe(
      'text-negative',
    )
    expect(regimeDisplay('growth', 'neutral').toneClass).toBe('text-warning')
  })

  it('keeps recession visually bearish but labelled apart from a bear market', () => {
    const display = regimeDisplay('recession', 'recession')

    expect(display.stance).toBe('bearish')
    expect(display.stanceLabel).toBe('Recession')
  })

  it('still renders a regime class this build does not know', () => {
    const display = regimeDisplay('stagflation_shock', 'neutral')

    expect(display.label).toBe('Stagflation shock')
    expect(display.explanation).toMatch(/data service/i)
  })

  it('falls back rather than rendering an empty title for a blank class', () => {
    expect(regimeDisplay('', 'neutral').label).toBe('Unclassified')
  })

  it('does not treat an inherited object key as a known regime class', () => {
    const display = regimeDisplay('toString', 'bull')

    expect(display.label).toBe('ToString')
    expect(display.explanation).toMatch(/data service/i)
  })
})

describe('toRegimeVisualIndicator', () => {
  it('passes through the indicators the service stores', () => {
    expect(toRegimeVisualIndicator('bull')).toBe('bull')
    expect(toRegimeVisualIndicator('bear')).toBe('bear')
    expect(toRegimeVisualIndicator('recession')).toBe('recession')
  })

  it('treats anything else as neutral, matching the service fallback', () => {
    expect(toRegimeVisualIndicator('sideways')).toBe('neutral')
    expect(toRegimeVisualIndicator('')).toBe('neutral')
    expect(toRegimeVisualIndicator('constructor')).toBe('neutral')
  })
})

describe('confidence', () => {
  it('clamps to the 0-100 the service constrains it to', () => {
    expect(clampConfidence(-10)).toBe(0)
    expect(clampConfidence(140)).toBe(100)
    expect(clampConfidence(72.4)).toBe(72.4)
  })

  it('treats a non-numeric confidence as zero rather than NaN on screen', () => {
    expect(clampConfidence(Number.NaN)).toBe(0)
    expect(formatConfidence(Number.NaN)).toBe('0%')
  })

  it('formats to whole percent', () => {
    expect(formatConfidence(72.4)).toBe('72%')
    expect(formatConfidence(72.6)).toBe('73%')
  })

  it('colours high confidence green, moderate amber, and low red', () => {
    expect(confidenceDisplay(HIGH_CONFIDENCE_MIN)).toMatchObject({
      band: 'high',
      toneClass: 'text-positive',
      barClass: 'bg-positive',
    })
    expect(confidenceDisplay(MODERATE_CONFIDENCE_MIN)).toMatchObject({
      band: 'moderate',
      toneClass: 'text-warning',
      barClass: 'bg-warning',
    })
    expect(confidenceDisplay(MODERATE_CONFIDENCE_MIN - 0.1)).toMatchObject({
      band: 'low',
      toneClass: 'text-negative',
      barClass: 'bg-negative',
    })
  })

  it('names each confidence band and its range', () => {
    expect(formatConfidenceBand('low')).toBe('Low')
    expect(formatConfidenceBandRange('low')).toBe(
      `<${MODERATE_CONFIDENCE_MIN}%`,
    )
    expect(formatConfidenceBandRange('moderate')).toBe(
      `${MODERATE_CONFIDENCE_MIN}–${HIGH_CONFIDENCE_MIN - 1}%`,
    )
    expect(formatConfidenceBandRange('high')).toBe(`≥${HIGH_CONFIDENCE_MIN}%`)
  })
})

describe('formatRegimeIdentifiedAt', () => {
  it('prints the classification time in 24-hour UTC', () => {
    expect(formatRegimeIdentifiedAt('2024-06-15T01:00:00.000Z')).toBe(
      'Jun 15, 01:00 UTC',
    )
  })

  it('does not roll midnight over to 24:00', () => {
    expect(formatRegimeIdentifiedAt('2024-06-15T00:00:00.000Z')).toBe(
      'Jun 15, 00:00 UTC',
    )
  })

  it('reads a local-time payload in UTC, not the reader’s zone', () => {
    expect(formatRegimeIdentifiedAt('2024-06-15T23:30:00.000Z')).toBe(
      'Jun 15, 23:30 UTC',
    )
  })

  it('says so rather than printing "Invalid Date" for an unreadable stamp', () => {
    expect(formatRegimeIdentifiedAt('not-a-date')).toBe('an unknown time')
  })
})
