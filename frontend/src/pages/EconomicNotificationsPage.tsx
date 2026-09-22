import { MacroAlertHistory } from '@/components/alerts/macro/MacroAlertHistory'
import { PageIntro } from '@/components/layout/PageIntro'
import { ALERTS_USER_ID } from '@/constants/alerts'
import { pageCopy } from '@/constants/navigation'

export function EconomicNotificationsPage() {
  const page = pageCopy.economicNotifications

  return (
    <div className="flex min-w-0 flex-col gap-4 sm:gap-6">
      <PageIntro description={page.body} />
      <MacroAlertHistory userId={ALERTS_USER_ID} />
    </div>
  )
}
