import { useState } from 'react'
import { SimilarPeriodCard } from '@/components/dashboard/regime/SimilarPeriodCard'
import { SimilarPeriodDetailsDialog } from '@/components/dashboard/regime/SimilarPeriodDetailsDialog'
import { Badge } from '@/components/ui/badge'
import { Skeleton } from '@/components/ui/skeleton'
import { useSimilarPeriodsQuery } from '@/hooks/useSimilarPeriodsQuery'
import type { SimilarPeriod } from '@/types/regime'

/** Historical periods whose macro backdrop resembles today's. */
export function SimilarPeriodsSection() {
  const { data, isPending, isError } = useSimilarPeriodsQuery()
  const [selectedId, setSelectedId] = useState<string | null>(null)

  const periods = data?.periods ?? []
  const selected = periods.find((period) => period.id === selectedId) ?? null

  return (
    <section
      aria-label="Similar historical periods"
      className="flex min-w-0 flex-col gap-3 overflow-hidden rounded-xl border border-border bg-card p-3 text-card-foreground sm:p-4"
    >
      <div className="flex min-w-0 flex-col gap-1">
        <div className="flex flex-wrap items-center gap-2">
          <h2 className="text-sm font-medium">Similar periods</h2>
          {data?.source === 'simulated' ? (
            <Badge variant="outline" className="text-[10px] font-normal">
              Simulated
            </Badge>
          ) : null}
        </div>
        <p className="text-xs text-muted-foreground">
          When the macro backdrop last looked like it does now, and what
          Bitcoin did next. Not a forecast — a comparison.
        </p>
      </div>

      {renderBody(isPending, isError, periods, setSelectedId)}

      <SimilarPeriodDetailsDialog
        period={selected}
        currentConditions={data?.currentConditions ?? {}}
        onClose={() => setSelectedId(null)}
      />
    </section>
  )
}

function renderBody(
  isPending: boolean,
  isError: boolean,
  periods: SimilarPeriod[],
  onSelect: (periodId: string) => void,
) {
  if (isPending) {
    return (
      <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
        {[0, 1, 2].map((key) => (
          <Skeleton key={key} className="h-32 w-full" />
        ))}
      </div>
    )
  }

  if (isError) {
    return (
      <p role="alert" className="py-6 text-center text-xs text-negative">
        Similar periods unavailable — retrying automatically
      </p>
    )
  }

  if (periods.length === 0) {
    return (
      <p className="py-6 text-center text-xs text-muted-foreground">
        No comparable period was found — the service needs more indicator
        history before it can match today against the past.
      </p>
    )
  }

  return (
    <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
      {periods.map((period) => (
        <SimilarPeriodCard
          key={period.id}
          period={period}
          onSelect={onSelect}
        />
      ))}
    </div>
  )
}
