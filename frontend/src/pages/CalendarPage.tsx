import { EconomicCalendar } from '@/components/calendar/EconomicCalendar'
import { PageIntro } from '@/components/layout/PageIntro'
import { ALERTS_USER_ID } from '@/constants/alerts'
import { pageCopy } from '@/constants/navigation'

export function CalendarPage() {
  const page = pageCopy.calendar

  return (
    <div className="flex min-w-0 flex-col gap-4 sm:gap-6">
      <PageIntro description={page.body} />
      <EconomicCalendar userId={ALERTS_USER_ID} />
    </div>
  )
}
