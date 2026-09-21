import type {
  EconomicEvent,
  EconomicEventType,
  EventImpactLevel,
} from '@/types/economicCalendar'

export const ECONOMIC_CALENDAR_MOCK_LATENCY_MS = 180

type SeedEvent = {
  event_name: string
  event_type: EconomicEventType
  impact_level: EventImpactLevel
  description: string
  /** Day of the month the release lands on. */
  day: number
  /** Release time, UTC, as `HH:MM`. */
  time: string
}

/**
 * A representative release calendar: the recurring US prints that move BTC,
 * on roughly the days of the month they actually land on.
 */
const SEED_EVENTS: SeedEvent[] = [
  {
    event_name: 'CPI release',
    event_type: 'cpi',
    impact_level: 'high',
    description:
      'Monthly consumer price index. A hotter print pushes rate-cut expectations out and usually weighs on BTC.',
    day: 12,
    time: '13:30',
  },
  {
    event_name: 'Non-farm payrolls',
    event_type: 'employment',
    impact_level: 'high',
    description:
      'Headline US jobs report. Strong hiring supports the dollar and tends to pressure risk assets including BTC.',
    day: 6,
    time: '13:30',
  },
  {
    event_name: 'FOMC rate decision',
    event_type: 'fed',
    impact_level: 'high',
    description:
      'Federal Reserve policy decision and statement. The single largest scheduled source of BTC volatility.',
    day: 19,
    time: '19:00',
  },
  {
    event_name: 'FOMC minutes',
    event_type: 'fed',
    impact_level: 'medium',
    description:
      'Minutes of the previous policy meeting. Moves BTC when they reveal a split committee.',
    day: 27,
    time: '19:00',
  },
  {
    event_name: 'GDP (second estimate)',
    event_type: 'gdp',
    impact_level: 'medium',
    description:
      'Revision to quarterly growth. A large miss shifts the recession narrative that drives risk appetite.',
    day: 22,
    time: '13:30',
  },
  {
    event_name: 'Initial jobless claims',
    event_type: 'employment',
    impact_level: 'low',
    description:
      'Weekly claims. Rarely market-moving on its own, but watched for a turn in the labour market.',
    day: 14,
    time: '13:30',
  },
]

export function delay(ms: number) {
  return new Promise((resolve) => setTimeout(resolve, ms))
}

function monthStart(reference: Date, monthOffset: number): Date {
  return new Date(
    Date.UTC(
      reference.getUTCFullYear(),
      reference.getUTCMonth() + monthOffset,
      1,
    ),
  )
}

function buildMonthEvents(
  month: Date,
  monthOffset: number,
): EconomicEvent[] {
  return SEED_EVENTS.map((seed, index) => {
    const [hours, minutes] = seed.time.split(':').map(Number)
    const eventDate = new Date(
      Date.UTC(
        month.getUTCFullYear(),
        month.getUTCMonth(),
        seed.day,
        hours,
        minutes,
      ),
    )

    return {
      // Stable within a run so React keys and dialog state stay put.
      id: (monthOffset + 1) * 100 + index,
      event_name: seed.event_name,
      event_type: seed.event_type,
      event_date: eventDate.toISOString(),
      impact_level: seed.impact_level,
      description: seed.description,
      dataSource: 'simulated' as const,
    }
  })
}

/**
 * Stand-in calendar for a frontend-only run, spanning last month through next
 * month so paging the grid always lands on something. Anchored to the current
 * date, and labelled simulated so it is never mistaken for the real schedule.
 */
export async function simulateEconomicCalendar(
  now: Date = new Date(),
): Promise<EconomicEvent[]> {
  await delay(ECONOMIC_CALENDAR_MOCK_LATENCY_MS)

  return [-1, 0, 1].flatMap((monthOffset) =>
    buildMonthEvents(monthStart(now, monthOffset), monthOffset),
  )
}
