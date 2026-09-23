import { PredictionPanel } from '@/components/dashboard/predictions/PredictionPanel'
import { PageIntro } from '@/components/layout/PageIntro'
import { pageCopy } from '@/constants/navigation'

export function ForecastsPage() {
  const page = pageCopy.forecasts

  return (
    <div className="flex min-w-0 flex-col gap-4 sm:gap-6">
      <PageIntro description={page.body} />

      <PredictionPanel />
    </div>
  )
}
