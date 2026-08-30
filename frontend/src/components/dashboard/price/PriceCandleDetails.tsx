import { formatPrice } from '@/components/dashboard/lib/priceFormat'
import {
  candleDirection,
  candleExtremePercents,
} from '@/components/dashboard/lib/candleGeometry'
import { getIndicatorChangeDisplay } from '@/lib/indicatorBtcImpact'
import { formatIndicatorTitle } from '@/lib/macroIndicatorHistory'
import { indicatorSeriesColor } from '@/lib/indicatorSeriesColor'
import { cn } from '@/lib/utils'
import { PriceCandleGlyph } from '@/components/dashboard/price/PriceCandleGlyph'
import { PriceCandleExtremeNote } from '@/components/dashboard/price/PriceCandleExtremeNote'
import type { ChartCandle } from '@/types/chart'

const OHLC_ROWS = [
  { key: 'open', label: 'Open' },
  { key: 'high', label: 'High' },
  { key: 'low', label: 'Low' },
  { key: 'close', label: 'Close' },
] as const

const BODY_KEYS = new Set<(typeof OHLC_ROWS)[number]['key']>(['open', 'close'])

type PriceCandleDetailsProps = {
  candle: ChartCandle
}

/** OHLC rows plus as-of macro change for a selected candle. */
export function PriceCandleDetails({ candle }: PriceCandleDetailsProps) {
  const prints = candle.asOfIndicators
    ? Object.entries(candle.asOfIndicators)
    : []
  const direction = candleDirection(candle)
  const bodyTone = direction === 'up' ? 'text-positive' : 'text-negative'
  const extremes = candleExtremePercents(candle)
  const extremeByKey = {
    high: { changePercent: extremes.highFromOpen, reference: 'open' as const },
    low: { changePercent: extremes.lowFromClose, reference: 'close' as const },
  }

  return (
    <>
      <p className={cn('mb-1 font-medium', bodyTone)}>
        {candle.time}
        <span className="ml-2 font-normal">
          {direction === 'up' ? 'Bullish' : 'Bearish'}
        </span>
      </p>
      <div className="flex items-stretch gap-2">
        <PriceCandleGlyph candle={candle} />
        <dl className="grid min-w-0 flex-1 grid-cols-[auto_1fr] gap-x-3 gap-y-0.5">
          {OHLC_ROWS.map((row) => {
            const extreme =
              row.key === 'high' || row.key === 'low'
                ? extremeByKey[row.key]
                : null

            return (
              <div key={row.key} className="contents">
                <dt className="text-muted-foreground">{row.label}</dt>
                <dd
                  className={cn(
                    'text-right font-mono tabular-nums',
                    BODY_KEYS.has(row.key) && bodyTone,
                  )}
                >
                  {formatPrice(candle[row.key])}
                  {extreme ? ' ' : null}
                  {extreme ? (
                    <PriceCandleExtremeNote
                      changePercent={extreme.changePercent}
                      reference={extreme.reference}
                    />
                  ) : null}
                </dd>
              </div>
            )
          })}
        </dl>
      </div>
      {prints.length > 0 ? (
        <dl className="mt-1.5 grid grid-cols-[auto_1fr] gap-x-3 gap-y-0.5 border-t border-border pt-1.5">
          {prints.map(([name, print]) => {
            const change = getIndicatorChangeDisplay(name, print.changePercent)

            return (
              <div key={name} className="contents">
                <dt
                  className="uppercase"
                  style={{ color: indicatorSeriesColor(name) }}
                >
                  {formatIndicatorTitle(name)}
                </dt>
                <dd
                  className={cn(
                    'text-right font-mono tabular-nums',
                    change.toneClass,
                  )}
                >
                  {change.text}
                </dd>
              </div>
            )
          })}
        </dl>
      ) : null}
    </>
  )
}
