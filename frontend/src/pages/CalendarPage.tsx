import { EconomicCalendar } from '@/components/calendar/EconomicCalendar'
import { ALERTS_USER_ID } from '@/constants/alerts'

export function CalendarPage() {
  return (
    <div className="flex min-w-0 flex-col">
      <EconomicCalendar userId={ALERTS_USER_ID} />
    </div>
  )
}
