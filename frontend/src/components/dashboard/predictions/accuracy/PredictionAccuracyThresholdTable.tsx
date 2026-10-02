import { Badge } from '@/components/ui/badge'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import {
  accuracyMetricLabel,
  formatThresholdRule,
  formatThresholdValue,
  thresholdToneClass,
} from '@/lib/predictionAccuracy'
import { cn } from '@/lib/utils'
import type { AccuracyThreshold } from '@/types/predictionAccuracy'

type PredictionAccuracyThresholdTableProps = {
  thresholds: AccuracyThreshold[]
}

function thresholdStatus(threshold: AccuracyThreshold) {
  if (threshold.warning) {
    return { label: 'Warning', className: 'border-warning text-warning' }
  }
  if (threshold.breached) {
    return { label: 'Watch', className: 'text-muted-foreground' }
  }
  return { label: 'OK', className: 'border-positive text-positive' }
}

/** Each quality bound the service checks, and where the model sits against it. */
export function PredictionAccuracyThresholdTable({
  thresholds,
}: PredictionAccuracyThresholdTableProps) {
  if (thresholds.length === 0) {
    return (
      <p className="text-sm text-muted-foreground">
        No quality checks were run for this window.
      </p>
    )
  }

  return (
    <Table aria-label="Quality checks">
      <TableHeader>
        <TableRow>
          <TableHead>Check</TableHead>
          <TableHead className="text-right">Now</TableHead>
          <TableHead>Rule</TableHead>
          <TableHead className="text-right">Status</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {thresholds.map((threshold) => {
          const status = thresholdStatus(threshold)
          return (
            <TableRow key={threshold.metric}>
              <TableCell>{accuracyMetricLabel(threshold.metric)}</TableCell>
              <TableCell
                className={cn(
                  'text-right tabular-nums',
                  thresholdToneClass(threshold),
                )}
              >
                {formatThresholdValue(threshold)}
              </TableCell>
              <TableCell className="text-muted-foreground">
                {formatThresholdRule(threshold)}
              </TableCell>
              <TableCell className="text-right">
                <Badge
                  variant="outline"
                  className={cn('text-[10px] font-normal', status.className)}
                >
                  {status.label}
                </Badge>
              </TableCell>
            </TableRow>
          )
        })}
      </TableBody>
    </Table>
  )
}
