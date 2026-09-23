import { RegimeConfidenceMeter } from '@/components/dashboard/regime/RegimeConfidenceMeter'
import { RegimeStanceBadge } from '@/components/dashboard/regime/RegimeStanceBadge'
import { Badge } from '@/components/ui/badge'
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'
import { Skeleton } from '@/components/ui/skeleton'
import { useCurrentRegimeQuery } from '@/hooks/useCurrentRegimeQuery'
import { formatRegimeIdentifiedAt, regimeDisplay } from '@/lib/regimeDisplay'
import { cn } from '@/lib/utils'
import type { CurrentRegime, RegimeDisplay } from '@/types/regime'

/** The macro backdrop the service has classified, alongside the price cards. */
export function RegimeCard() {
  const { data, isPending, isError } = useCurrentRegimeQuery()
  const display = data
    ? regimeDisplay(data.regimeType, data.visualIndicator)
    : null

  return (
    <Card className="min-w-0 sm:col-span-2 lg:col-span-1">
      <CardHeader>
        <CardDescription className="flex flex-wrap items-center gap-2">
          Macro regime
          {data?.source === 'simulated' ? (
            <Badge variant="outline" className="text-[10px] font-normal">
              Simulated
            </Badge>
          ) : null}
        </CardDescription>
        <CardTitle className="min-w-0 text-base sm:text-lg lg:text-xl">
          {renderTitle(isPending, display)}
        </CardTitle>
      </CardHeader>

      <CardContent className="flex min-w-0 flex-col gap-3">
        {renderBody(isPending, isError, data, display)}
      </CardContent>
    </Card>
  )
}

function renderTitle(isPending: boolean, display: RegimeDisplay | null) {
  if (isPending) {
    return <Skeleton className="h-5 w-28 sm:h-6 sm:w-36" />
  }

  // No classification to name — an error and an empty backdrop both land here,
  // and the body below says which of the two it is.
  if (!display) {
    return <span className="text-muted-foreground">Not classified</span>
  }

  return (
    <span className={cn('min-w-0 truncate', display.toneClass)}>
      {display.label}
    </span>
  )
}

function renderBody(
  isPending: boolean,
  isError: boolean,
  regime: CurrentRegime | null | undefined,
  display: RegimeDisplay | null,
) {
  if (isPending) {
    return (
      <>
        <Skeleton className="h-5 w-20" />
        <Skeleton className="h-8 w-full" />
      </>
    )
  }

  if (isError) {
    return (
      <p role="alert" className="text-xs text-negative">
        Regime unavailable — retrying automatically
      </p>
    )
  }

  if (!regime || !display) {
    return (
      <p className="text-xs text-muted-foreground">
        The macro backdrop has not been classified yet — the service publishes
        its first read once it has enough indicator history.
      </p>
    )
  }

  return (
    <>
      <div className="flex flex-wrap items-center gap-2">
        <RegimeStanceBadge display={display} />
        <span className="text-xs text-muted-foreground">
          AI-classified market context
        </span>
      </div>

      <RegimeConfidenceMeter confidence={regime.confidence} />

      <p className="text-xs leading-relaxed text-muted-foreground">
        {display.explanation}
      </p>

      <p className="text-xs text-muted-foreground">
        {`Identified ${formatRegimeIdentifiedAt(regime.identifiedAt)}`}
      </p>
    </>
  )
}
