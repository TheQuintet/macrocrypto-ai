import { Badge } from '@/components/ui/badge'
import { cn } from '@/lib/utils'
import type { RegimeDisplay } from '@/types/regime'

type RegimeStanceBadgeProps = {
  display: RegimeDisplay
}

/** Bull / Bear / Recession — the service's own read on the regime. */
export function RegimeStanceBadge({ display }: RegimeStanceBadgeProps) {
  return (
    <Badge
      variant="outline"
      data-stance={display.stance}
      className={cn('font-medium', display.toneClass)}
    >
      {display.stanceLabel}
    </Badge>
  )
}
