import {
  ActivityIcon,
  MinusIcon,
  TrendingDownIcon,
  TrendingUpIcon,
  type LucideIcon,
} from 'lucide-react'
import { cn } from '@/lib/utils'
import type { MarketCondition } from '@/types/predictionAccuracy'

const MARKET_CONDITION_ICONS: Record<MarketCondition, LucideIcon> = {
  bull: TrendingUpIcon,
  bear: TrendingDownIcon,
  volatile: ActivityIcon,
  neutral: MinusIcon,
}

type MarketConditionIconProps = {
  condition: MarketCondition
  className?: string
}

/**
 * Which market a row is about, by shape rather than colour: next to it the
 * colour is the accuracy grade, and a red "bear" mark beside a green grade
 * would read as a contradiction.
 */
export function MarketConditionIcon({
  condition,
  className,
}: MarketConditionIconProps) {
  const Icon = MARKET_CONDITION_ICONS[condition]

  return (
    <Icon
      aria-hidden="true"
      data-market-condition={condition}
      className={cn('size-3.5 shrink-0 text-muted-foreground', className)}
    />
  )
}
