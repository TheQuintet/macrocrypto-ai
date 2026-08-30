import { PageHeader } from '@/components/layout/PageHeader'
import { MacroIndicatorsSection } from '@/components/dashboard/indicators/MacroIndicatorsSection'
import { pageCopy } from '@/constants/navigation'

export function MacroPage() {
  const page = pageCopy.macro

  return (
    <div className="flex min-w-0 flex-col gap-4 sm:gap-6">
      <PageHeader title={page.title} description={page.body} />

      <MacroIndicatorsSection />
    </div>
  )
}
