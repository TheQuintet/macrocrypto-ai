import { RegimePerformanceChart } from '@/components/dashboard/regime/RegimePerformanceChart'
import { RegimeExportButton } from '@/components/dashboard/regime/RegimeExportButton'
import { RegimePerformanceTable } from '@/components/dashboard/regime/RegimePerformanceTable'
import { Badge } from '@/components/ui/badge'
import { Skeleton } from '@/components/ui/skeleton'
import { useRegimePerformanceQuery } from '@/hooks/useRegimePerformanceQuery'
import type { RegimePerformanceRow } from '@/types/regime'

/** How BTC has behaved in each macro regime — chart plus the full metrics. */
export function RegimePerformanceSection() {
  const { data, isPending, isError } = useRegimePerformanceQuery()
  const rows = data?.rows ?? []

  return (
    <section
      aria-label="BTC performance by macro regime"
      className="flex min-w-0 flex-col gap-3 overflow-hidden rounded-xl border border-border bg-card p-3 text-card-foreground sm:p-4"
    >
      <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
        <div className="flex min-w-0 flex-col gap-1">
          <div className="flex flex-wrap items-center gap-2">
            <h2 className="text-sm font-medium">Performance by regime</h2>
            {data?.source === 'simulated' ? (
              <Badge variant="outline" className="text-[10px] font-normal">
                Simulated
              </Badge>
            ) : null}
          </div>
          <p className="text-xs text-muted-foreground">
            Average BTC return in each macro backdrop, with the drawdown,
            volatility, and Sharpe ratio behind it. Hover a bar for the full
            set.
          </p>
        </div>

        {rows.length > 0 ? (
          <RegimeExportButton rows={rows} source={data?.source ?? 'live'} />
        ) : null}
      </div>

      {renderBody(isPending, isError, rows)}
    </section>
  )
}

function renderBody(
  isPending: boolean,
  isError: boolean,
  rows: RegimePerformanceRow[],
) {
  if (isPending) {
    return (
      <div className="flex flex-col gap-3">
        <Skeleton className="h-56 w-full" />
        <Skeleton className="h-24 w-full" />
      </div>
    )
  }

  if (isError) {
    return (
      <p role="alert" className="py-6 text-center text-xs text-negative">
        Regime performance unavailable — retrying automatically
      </p>
    )
  }

  if (rows.length === 0) {
    return (
      <p className="py-6 text-center text-xs text-muted-foreground">
        No regimes have been measured yet — the service publishes these once it
        has classified a full period.
      </p>
    )
  }

  return (
    <div className="flex min-w-0 flex-col gap-4">
      <RegimePerformanceChart rows={rows} />
      <RegimePerformanceTable rows={rows} />
    </div>
  )
}
