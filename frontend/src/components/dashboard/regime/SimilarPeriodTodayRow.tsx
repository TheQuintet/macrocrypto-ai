import { Badge } from '@/components/ui/badge'
import { TableCell, TableRow } from '@/components/ui/table'
import { formatConditionValue } from '@/lib/similarPeriodIndicators'

type SimilarPeriodTodayRowProps = {
  conditions: Record<string, number>
  indicators: string[]
}

/** Today's prints as a table row so they line up with each historical match. */
export function SimilarPeriodTodayRow({
  conditions,
  indicators,
}: SimilarPeriodTodayRowProps) {
  return (
    <TableRow
      data-current-conditions=""
      aria-label="Current macro conditions"
      className="bg-muted/40 hover:bg-muted/40"
    >
      <TableCell className="min-w-0 font-medium">
        <div className="flex flex-wrap items-center gap-1.5">
          <span>Today</span>
          <Badge variant="outline" className="text-[10px] font-normal">
            Now
          </Badge>
        </div>
      </TableCell>
      <TableCell className="text-muted-foreground">—</TableCell>
      <TableCell className="text-right text-muted-foreground">—</TableCell>
      {indicators.map((indicator) => (
        <TableCell
          key={indicator}
          data-indicator={indicator}
          className="text-right font-medium tabular-nums"
        >
          {formatConditionValue(conditions[indicator])}
        </TableCell>
      ))}
      <TableCell className="hidden text-muted-foreground sm:table-cell">
        The prints the matches are measured against.
      </TableCell>
    </TableRow>
  )
}
