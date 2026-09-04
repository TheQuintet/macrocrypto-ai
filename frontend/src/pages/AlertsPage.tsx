import { AlertManagement } from '@/components/alerts/AlertManagement'
import { ALERTS_USER_ID } from '@/constants/alerts'

/** Title lives in the breadcrumb; the page leads with its tabs. */
export function AlertsPage() {
  return (
    <div className="flex min-w-0 flex-col gap-4 sm:gap-6">
      <AlertManagement userId={ALERTS_USER_ID} />
    </div>
  )
}
