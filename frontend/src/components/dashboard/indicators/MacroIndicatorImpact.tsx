import { getIndicatorChangeDisplay } from '@/lib/indicatorBtcImpact'
import { cn } from '@/lib/utils'
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from '@/components/ui/tooltip'

type MacroIndicatorImpactProps = {
  indicatorName: string
  changePercent: number | null
}

/** Colored % change with a tooltip explaining the BTC impact. */
export function MacroIndicatorImpact({
  indicatorName,
  changePercent,
}: MacroIndicatorImpactProps) {
  const change = getIndicatorChangeDisplay(indicatorName, changePercent)

  return (
    <Tooltip>
      <TooltipTrigger asChild>
        <button
          type="button"
          className={cn(
            'inline-flex min-h-11 items-center rounded-md px-1.5 text-sm font-medium sm:min-h-7',
            'touch-manipulation focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring/50',
            change.toneClass,
          )}
          aria-label={`${change.formatted}, ${change.label}`}
        >
          {change.text}
        </button>
      </TooltipTrigger>
      <TooltipContent className="flex max-w-[min(20rem,calc(100vw-2rem))] flex-col items-start gap-0.5">
        <span className="font-medium">{change.label}</span>
        <span>{change.reason}</span>
      </TooltipContent>
    </Tooltip>
  )
}
