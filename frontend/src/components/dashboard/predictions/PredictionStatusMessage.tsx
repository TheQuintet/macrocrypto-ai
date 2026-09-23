import { Skeleton } from '@/components/ui/skeleton'

type PredictionStatusMessageProps = {
  isPending: boolean
  error: Error | null
  /** Rendered while loading — a chart pane needs a taller block than a stat list. */
  skeletonClassName?: string
}

/**
 * Loading and failure states shared by the forecast cards.
 *
 * A failed request says so rather than falling back to invented numbers: the
 * simulated batch only stands in when no backend is configured at all.
 */
export function PredictionStatusMessage({
  isPending,
  error,
  skeletonClassName = 'h-40 w-full',
}: PredictionStatusMessageProps) {
  if (isPending) {
    return <Skeleton className={skeletonClassName} />
  }

  if (error) {
    return (
      <div role="alert" className="flex flex-col gap-1">
        <p className="text-sm text-negative">Forecast unavailable</p>
        <p className="text-xs text-muted-foreground">{error.message}</p>
      </div>
    )
  }

  return (
    <p className="text-sm text-muted-foreground">
      No forecast available for this window
    </p>
  )
}
