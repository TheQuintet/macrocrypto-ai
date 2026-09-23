import { indicatorSeriesColor } from '@/lib/indicatorSeriesColor'
import { similarPeriodIndicatorLabel } from '@/lib/similarPeriodIndicators'
import { cn } from '@/lib/utils'

type SimilarPeriodIndicatorLabelProps = {
  name: string
  className?: string
}

/** Indicator name in the same series color the macro cards use. */
export function SimilarPeriodIndicatorLabel({
  name,
  className,
}: SimilarPeriodIndicatorLabelProps) {
  const color = indicatorSeriesColor(name)

  return (
    <span className={cn('inline-flex min-w-0 items-center gap-1.5', className)}>
      <span
        aria-hidden
        className="size-2 shrink-0 rounded-full"
        style={{ backgroundColor: color }}
      />
      <span className="truncate" style={{ color }}>
        {similarPeriodIndicatorLabel(name)}
      </span>
    </span>
  )
}
