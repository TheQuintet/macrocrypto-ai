import { useState } from 'react'
import { IndicatorPeriodPicker } from '@/components/dashboard/indicators/IndicatorPeriodPicker'
import { IndicatorViewToggle } from '@/components/dashboard/indicators/IndicatorViewToggle'
import { MacroIndicatorHistory } from '@/components/dashboard/indicators/MacroIndicatorHistory'
import { MacroIndicators } from '@/components/dashboard/MacroIndicators'
import { useMacroIndicatorHistoryQuery } from '@/hooks/useMacroIndicatorHistoryQuery'
import { useMacroIndicatorsQuery } from '@/hooks/useMacroIndicatorsQuery'
import type {
  MacroIndicatorPeriod,
  MacroIndicatorView,
} from '@/types/macroIndicators'

type MacroIndicatorsSectionProps = {
  allowHistory?: boolean
}

export function MacroIndicatorsSection({
  allowHistory = false,
}: MacroIndicatorsSectionProps) {
  const [view, setView] = useState<MacroIndicatorView>('current')
  const [period, setPeriod] = useState<MacroIndicatorPeriod>('90d')
  const latestQuery = useMacroIndicatorsQuery()
  const historyQuery = useMacroIndicatorHistoryQuery(
    period,
    allowHistory && view === 'historical',
  )

  const showHistory = allowHistory && view === 'historical'

  return (
    <div className="flex min-w-0 flex-col gap-3">
      {allowHistory ? (
        <div className="flex flex-col gap-2 sm:flex-row sm:flex-wrap sm:items-center sm:justify-between">
          <IndicatorViewToggle value={view} onChange={setView} />
          {showHistory ? (
            <IndicatorPeriodPicker value={period} onChange={setPeriod} />
          ) : null}
        </div>
      ) : null}

      {showHistory ? (
        <MacroIndicatorHistory
          indicators={historyQuery.data ?? []}
          isLoading={historyQuery.isPending}
          error={historyQuery.error}
        />
      ) : (
        <MacroIndicators
          indicators={latestQuery.data ?? []}
          isLoading={latestQuery.isPending}
          error={latestQuery.error}
        />
      )}
    </div>
  )
}
