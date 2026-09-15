import { describe, expect, it } from 'vitest'
import { buildRegimeCsv, regimeCsvFileName } from '@/lib/regimeExport'
import type { RegimePerformanceRow } from '@/types/regime'

const NOW = Date.parse('2024-06-15T09:00:00Z')

function row(
  overrides: Partial<RegimePerformanceRow> = {},
): RegimePerformanceRow {
  return {
    regimeId: 4,
    regimeType: 'growth',
    startDate: '2023-08-01',
    endDate: '2024-02-29',
    status: 'completed',
    performance: {
      avgReturn: 28.4,
      maxDrawdown: -11.2,
      volatility: 36.8,
      sharpeRatio: 1.42,
      btcPriceStart: 47_800,
      btcPriceEnd: 61_400,
    },
    ...overrides,
  }
}

const ACTIVE = row({
  regimeId: 5,
  regimeType: 'rising_rates',
  startDate: '2024-03-01',
  endDate: null,
  status: 'active',
})

function lines(csv: string) {
  return csv.split('\r\n')
}

describe('buildRegimeCsv', () => {
  it('names the data source so a simulated file cannot be mistaken for real', () => {
    const csv = buildRegimeCsv({ rows: [row()], source: 'simulated', nowMs: NOW })

    expect(csv).toContain('# Data source,Simulated')
  })

  it('marks a live export as live', () => {
    const csv = buildRegimeCsv({ rows: [row()], source: 'live', nowMs: NOW })

    expect(csv).toContain('# Data source,Live')
  })

  it('stamps when the file was taken', () => {
    const csv = buildRegimeCsv({ rows: [row()], source: 'live', nowMs: NOW })

    expect(csv).toContain('# Exported at,2024-06-15T09:00:00.000Z')
  })

  it('carries every metric the table shows', () => {
    const csv = buildRegimeCsv({ rows: [row()], source: 'live', nowMs: NOW })
    const header = lines(csv).find((line) => line.startsWith('Regime,'))

    for (const column of [
      'Avg return %',
      'Max drawdown %',
      'Volatility %',
      'Sharpe ratio',
      'BTC price start',
      'BTC price end',
    ]) {
      expect(header).toContain(column)
    }
  })

  it('exports the rows it was given, newest regime first', () => {
    const csv = buildRegimeCsv({
      rows: [row(), ACTIVE],
      source: 'live',
      nowMs: NOW,
    })
    const body = lines(csv).filter((line) => line.startsWith('Rising') || line.startsWith('Growth'))

    expect(body[0]).toContain('rising_rates')
    expect(body[1]).toContain('growth')
  })

  it('exports only the rows on screen', () => {
    // The button is handed the rendered rows, so a filtered view exports
    // filtered data rather than silently widening to everything.
    const csv = buildRegimeCsv({ rows: [ACTIVE], source: 'live', nowMs: NOW })

    expect(csv).toContain('# Regimes,1')
    expect(csv).not.toContain('growth')
  })

  it('leaves an open regime with an empty end date', () => {
    const csv = buildRegimeCsv({ rows: [ACTIVE], source: 'live', nowMs: NOW })
    const line = lines(csv).find((row_) => row_.startsWith('Rising rates'))

    expect(line).toContain('active')
    expect(line).toContain('2024-03-01,,')
  })

  it('writes a missing metric as blank, not as zero', () => {
    const csv = buildRegimeCsv({
      rows: [
        row({
          performance: { ...row().performance, sharpeRatio: null },
        }),
      ],
      source: 'live',
      nowMs: NOW,
    })
    const line = lines(csv).find((row_) => row_.startsWith('Growth'))

    expect(line).toContain('36.8,,')
  })

  it('still produces a usable file with no regimes', () => {
    const csv = buildRegimeCsv({ rows: [], source: 'live', nowMs: NOW })

    expect(csv).toContain('# Regimes,0')
    expect(csv).toContain('Avg return %')
  })
})

describe('regimeCsvFileName', () => {
  it('is dated so repeated exports do not overwrite each other', () => {
    expect(regimeCsvFileName(NOW)).toBe('regime-performance-2024-06-15.csv')
  })
})
