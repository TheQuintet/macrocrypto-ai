import { Badge } from '@/components/ui/badge'
import { cn } from '@/lib/utils'
import type { PredictionTrend } from '@/types/predictions'

const trendConfig: Record<
  PredictionTrend,
  { label: string; glyph: string; className: string }
> = {
  up: { label: 'Up', glyph: '↑', className: 'text-positive' },
  down: { label: 'Down', glyph: '↓', className: 'text-negative' },
  neutral: { label: 'Neutral', glyph: '→', className: 'text-muted-foreground' },
}

type PredictionTrendBadgeProps = {
  trend: PredictionTrend
}

/** Direction the model expects over the selected window. */
export function PredictionTrendBadge({ trend }: PredictionTrendBadgeProps) {
  const config = trendConfig[trend]

  return (
    <Badge
      variant="outline"
      className={cn('gap-1 font-medium', config.className)}
      aria-label={`Trend ${config.label.toLowerCase()}`}
    >
      <span aria-hidden="true">{config.glyph}</span>
      {config.label}
    </Badge>
  )
}
