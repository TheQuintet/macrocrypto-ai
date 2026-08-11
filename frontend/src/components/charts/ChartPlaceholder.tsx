import { cn } from '@/lib/utils'

type ChartPlaceholderProps = {
  className?: string
  label?: string
}

/** Calm wireframe chart area — layout reads as a chart without fake data. */
export function ChartPlaceholder({
  className,
  label = 'Chart area',
}: ChartPlaceholderProps) {
  return (
    <div
      className={cn(
        'relative w-full overflow-hidden rounded-md border border-dashed bg-muted/30',
        className,
      )}
      role="img"
      aria-label={`${label} placeholder`}
    >
      <div className="absolute inset-0 flex flex-col justify-between p-px">
        {Array.from({ length: 5 }).map((_, index) => (
          <div key={index} className="h-px w-full bg-border/60" />
        ))}
      </div>

      <svg
        className="absolute inset-0 h-full w-full text-primary/50"
        viewBox="0 0 100 40"
        preserveAspectRatio="none"
        aria-hidden="true"
      >
        <polyline
          points="0,30 12,26 24,29 36,20 48,23 60,14 72,17 84,9 100,12"
          fill="none"
          stroke="currentColor"
          strokeWidth="0.8"
          vectorEffect="non-scaling-stroke"
          strokeLinejoin="round"
          strokeLinecap="round"
        />
      </svg>

      <div className="absolute bottom-2 left-3 font-mono text-[0.7rem] uppercase tracking-wider text-muted-foreground">
        {label}
      </div>
    </div>
  )
}
