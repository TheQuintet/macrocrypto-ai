import { csvFileName, toCsv } from '@/lib/csv'
import { regimeDisplay } from '@/lib/regimeDisplay'
import { sortRegimesByStart } from '@/lib/regimePerformance'
import type { RegimePerformanceRow, RegimeSource } from '@/types/regime'

export const REGIME_EXPORT_FILE_PREFIX = 'regime-performance'

type RegimeExportOptions = {
  rows: RegimePerformanceRow[]
  source: RegimeSource
  nowMs?: number
}

/**
 * Regime metrics as CSV.
 *
 * Leads with a metadata block naming the data source and when the file was
 * taken. A sheet of returns with no provenance is the kind of thing that gets
 * pasted into a report six months later — it has to say on its face whether
 * it came from the live service or from simulated stand-ins.
 */
export function buildRegimeCsv({
  rows,
  source,
  nowMs = Date.now(),
}: RegimeExportOptions): string {
  const exported = sortRegimesByStart(rows).reverse()

  const metadata: (readonly unknown[])[] = [
    ['# MacroCrypto AI — BTC performance by macro regime'],
    ['# Data source', source === 'simulated' ? 'Simulated' : 'Live'],
    ['# Exported at', new Date(nowMs).toISOString()],
    ['# Regimes', exported.length],
    [],
  ]

  const header = [
    'Regime',
    'Regime type',
    'Status',
    'Start date',
    'End date',
    'Avg return %',
    'Max drawdown %',
    'Volatility %',
    'Sharpe ratio',
    'BTC price start',
    'BTC price end',
  ]

  const body = exported.map((row) => [
    regimeDisplay(row.regimeType, 'neutral').label,
    row.regimeType,
    row.status,
    row.startDate,
    row.endDate ?? '',
    row.performance.avgReturn,
    row.performance.maxDrawdown,
    row.performance.volatility,
    row.performance.sharpeRatio,
    row.performance.btcPriceStart,
    row.performance.btcPriceEnd,
  ])

  return toCsv([...metadata, header, ...body])
}

export function regimeCsvFileName(nowMs = Date.now()) {
  return csvFileName(REGIME_EXPORT_FILE_PREFIX, nowMs)
}
