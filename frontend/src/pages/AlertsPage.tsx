import { AlertManagement } from '@/components/alerts/AlertManagement'
import { PageHeader } from '@/components/layout/PageHeader'
import { ALERTS_USER_ID } from '@/constants/alerts'
import { pageCopy } from '@/constants/navigation'

export function AlertsPage() {
  const page = pageCopy.alerts

  return (
    <div className="flex min-w-0 flex-col gap-4 sm:gap-6">
      <PageHeader title={page.title} />
      <AlertManagement userId={ALERTS_USER_ID} />
    </div>
  )
}
