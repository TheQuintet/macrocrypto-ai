import type { RegimeHistoryRow, RegimeTimelineSegment } from '@/types/regime'

/** Zoom steps for the band, as a multiple of the container width. */
export const TIMELINE_ZOOM_LEVELS = [1, 2, 4, 8] as const

export const MIN_TIMELINE_ZOOM = TIMELINE_ZOOM_LEVELS[0]
export const MAX_TIMELINE_ZOOM =
  TIMELINE_ZOOM_LEVELS[TIMELINE_ZOOM_LEVELS.length - 1]

export function clampTimelineZoom(zoom: number) {
  return Math.min(MAX_TIMELINE_ZOOM, Math.max(MIN_TIMELINE_ZOOM, zoom))
}

/** Next step up or down the ladder, staying inside the range. */
export function stepTimelineZoom(zoom: number, direction: 1 | -1) {
  const current = clampTimelineZoom(zoom)
  const index = TIMELINE_ZOOM_LEVELS.indexOf(
    current as (typeof TIMELINE_ZOOM_LEVELS)[number],
  )

  if (index === -1) {
    return clampTimelineZoom(current * (direction === 1 ? 2 : 0.5))
  }

  const next = TIMELINE_ZOOM_LEVELS[index + direction]

  return next ?? current
}

/** Dates arrive as `YYYY-MM-DD`; read them in UTC so they do not shift a day. */
function toUtcMs(date: string) {
  const parsed = Date.parse(`${date}T00:00:00Z`)

  return Number.isNaN(parsed) ? null : parsed
}

/**
 * Lay the regimes out along a single band.
 *
 * An open regime runs to `nowMs` — the service marks it with a null end date,
 * and a segment with no end cannot be given a width.
 *
 * Rows whose start date cannot be read are dropped rather than positioned at
 * the epoch, which would stretch the whole band back to 1970.
 */
export function buildTimelineSegments(
  rows: RegimeHistoryRow[],
  nowMs: number,
): RegimeTimelineSegment[] {
  const dated = rows
    .map((row) => {
      const startMs = toUtcMs(row.startDate)

      if (startMs == null) {
        return null
      }

      const parsedEnd = row.endDate ? toUtcMs(row.endDate) : nowMs
      const endMs = parsedEnd == null ? nowMs : parsedEnd

      // A regime that ends before it starts is not layout-able; treat the end
      // as the start so it renders as a hairline rather than a negative width.
      return { row, startMs, endMs: Math.max(startMs, endMs) }
    })
    .filter((entry): entry is NonNullable<typeof entry> => entry !== null)
    .sort((a, b) => a.startMs - b.startMs)

  if (dated.length === 0) {
    return []
  }

  const domainStart = dated[0].startMs
  const domainEnd = Math.max(...dated.map((entry) => entry.endMs))
  const span = domainEnd - domainStart

  return dated.map((entry) => {
    if (span <= 0) {
      return { ...entry, offsetPercent: 0, widthPercent: 100 }
    }

    return {
      ...entry,
      offsetPercent: ((entry.startMs - domainStart) / span) * 100,
      widthPercent: ((entry.endMs - entry.startMs) / span) * 100,
    }
  })
}

export type TimelineTick = {
  label: string
  offsetPercent: number
}

/**
 * Year boundaries across the band, so the reader can date what they are
 * looking at. Months would crowd a multi-year span; the zoom control is what
 * gets you closer in.
 */
export function timelineYearTicks(
  segments: RegimeTimelineSegment[],
): TimelineTick[] {
  if (segments.length === 0) {
    return []
  }

  const domainStart = segments[0].startMs
  const domainEnd = Math.max(...segments.map((segment) => segment.endMs))
  const span = domainEnd - domainStart

  if (span <= 0) {
    return []
  }

  const firstYear = new Date(domainStart).getUTCFullYear()
  const lastYear = new Date(domainEnd).getUTCFullYear()
  const ticks: TimelineTick[] = []

  for (let year = firstYear + 1; year <= lastYear; year += 1) {
    const boundary = Date.UTC(year, 0, 1)

    if (boundary >= domainStart && boundary <= domainEnd) {
      ticks.push({
        label: String(year),
        offsetPercent: ((boundary - domainStart) / span) * 100,
      })
    }
  }

  return ticks
}
