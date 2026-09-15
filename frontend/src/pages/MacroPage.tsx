import { PageIntro } from '@/components/layout/PageIntro'
import { MacroIndicatorsSection } from '@/components/dashboard/indicators/MacroIndicatorsSection'
import { RegimePerformanceSection } from '@/components/dashboard/regime/RegimePerformanceSection'
import { RegimeTimelineSection } from '@/components/dashboard/regime/RegimeTimelineSection'
import { pageCopy } from '@/constants/navigation'

export function MacroPage() {
  const page = pageCopy.macro

  return (
    <div className="flex min-w-0 flex-col gap-4 sm:gap-6">
      <PageIntro description={page.body} />

      <MacroIndicatorsSection />

      <RegimeTimelineSection />

      <RegimePerformanceSection />
    </div>
  )
}
