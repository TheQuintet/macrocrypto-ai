import { useState } from 'react'
import { RegimePerformanceSection } from '@/components/dashboard/regime/RegimePerformanceSection'
import { RegimeTimelineSection } from '@/components/dashboard/regime/RegimeTimelineSection'
import { RegimeViewTabs } from '@/components/dashboard/regime/RegimeViewTabs'
import { SimilarPeriodsSection } from '@/components/dashboard/regime/SimilarPeriodsSection'
import { PageIntro } from '@/components/layout/PageIntro'
import { pageCopy } from '@/constants/navigation'
import type { RegimePageView } from '@/types/regime'

export function RegimePerformancePage() {
  const page = pageCopy.regimePerformance
  const [view, setView] = useState<RegimePageView>('performance')

  return (
    <div className="flex min-w-0 flex-col gap-4 sm:gap-6">
      <PageIntro description={page.body} />
      <RegimeViewTabs value={view} onChange={setView} />
      {view === 'performance' ? <RegimePerformanceSection /> : null}
      {view === 'timeline' ? <RegimeTimelineSection /> : null}
      {view === 'similarPeriods' ? <SimilarPeriodsSection /> : null}
    </div>
  )
}
