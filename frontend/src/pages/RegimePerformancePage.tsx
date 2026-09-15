import { RegimePerformanceSection } from '@/components/dashboard/regime/RegimePerformanceSection'
import { RegimeTimelineSection } from '@/components/dashboard/regime/RegimeTimelineSection'
import { SimilarPeriodsSection } from '@/components/dashboard/regime/SimilarPeriodsSection'
import { PageIntro } from '@/components/layout/PageIntro'
import { pageCopy } from '@/constants/navigation'

export function RegimePerformancePage() {
  const page = pageCopy.regimePerformance

  return (
    <div className="flex min-w-0 flex-col gap-4 sm:gap-6">
      <PageIntro description={page.body} />
      <RegimePerformanceSection />
      <RegimeTimelineSection />
      <SimilarPeriodsSection />
    </div>
  )
}
