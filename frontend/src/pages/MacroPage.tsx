import { PageHeader } from '@/components/layout/PageHeader'
import { TimeRangeBadge } from '@/components/timeRange/TimeRangeBadge'
import { MacroIndicators } from '@/components/dashboard/MacroIndicators'
import { useMacroIndicatorsQuery } from '@/hooks/useMacroIndicatorsQuery'
import { pageCopy } from '@/constants/navigation'

export function MacroPage() {
  const page = pageCopy.macro
  const { data: indicators, isLoading, error } = useMacroIndicatorsQuery()

  return (
    <div className="flex min-w-0 flex-col gap-4 sm:gap-6">
      <PageHeader title={page.title} description={page.body}>
        <TimeRangeBadge />
      </PageHeader>

      <MacroIndicators 
        indicators={indicators || []} 
        isLoading={isLoading}
        error={error}
      />
    </div>
  )
}