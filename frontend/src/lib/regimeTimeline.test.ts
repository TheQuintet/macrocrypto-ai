import { describe, expect, it } from 'vitest'
import {
  buildTimelineSegments,
  clampTimelineZoom,
  MAX_TIMELINE_ZOOM,
  MIN_TIMELINE_ZOOM,
  stepTimelineZoom,
  timelineYearTicks,
} from '@/lib/regimeTimeline'
import type { RegimeHistoryRow } from '@/types/regime'

const NOW = Date.parse('2024-07-01T00:00:00Z')

function historyRow(
  id: number,
  regimeType: string,
  startDate: string,
  endDate: string | null,
): RegimeHistoryRow {
  return {
    id,
    regimeType,
    startDate,
    endDate,
    isCurrent: endDate == null,
    performance: null,
  }
}

describe('buildTimelineSegments', () => {
  it('lays regimes out oldest first, whatever order the API sent', () => {
    const segments = buildTimelineSegments(
      [
        historyRow(2, 'growth', '2023-01-01', '2024-01-01'),
        historyRow(1, 'recession', '2022-01-01', '2023-01-01'),
      ],
      NOW,
    )

    expect(segments.map((segment) => segment.row.id)).toEqual([1, 2])
    expect(segments[0].offsetPercent).toBe(0)
  })

  it('gives each regime a width in proportion to how long it ran', () => {
    // 2022 and 2023 are the same length, so each takes half the band.
    const segments = buildTimelineSegments(
      [
        historyRow(1, 'recession', '2022-01-01', '2023-01-01'),
        historyRow(2, 'growth', '2023-01-01', '2024-01-01'),
      ],
      NOW,
    )

    expect(segments[0].widthPercent).toBeCloseTo(50, 0)
    expect(segments[1].widthPercent).toBeCloseTo(50, 0)
    expect(segments[1].offsetPercent).toBeCloseTo(50, 0)
  })

  it('runs an open regime to now, since it has no end to measure against', () => {
    const segments = buildTimelineSegments(
      [historyRow(1, 'rising_rates', '2024-01-01', null)],
      NOW,
    )

    expect(segments[0].endMs).toBe(NOW)
    expect(segments[0].widthPercent).toBe(100)
  })

  it('gives a single regime the whole band rather than dividing by zero', () => {
    const segments = buildTimelineSegments(
      [historyRow(1, 'growth', '2024-07-01', '2024-07-01')],
      NOW,
    )

    expect(segments).toHaveLength(1)
    expect(segments[0].offsetPercent).toBe(0)
    expect(segments[0].widthPercent).toBe(100)
  })

  it('drops a row whose start date cannot be read', () => {
    // Positioning it at the epoch would stretch the band back to 1970 and
    // squash every real regime into a sliver.
    const segments = buildTimelineSegments(
      [
        historyRow(1, 'growth', 'not-a-date', '2024-01-01'),
        historyRow(2, 'recession', '2023-01-01', '2024-01-01'),
      ],
      NOW,
    )

    expect(segments.map((segment) => segment.row.id)).toEqual([2])
  })

  it('never produces a negative width when the dates are inverted', () => {
    const segments = buildTimelineSegments(
      [historyRow(1, 'growth', '2024-06-01', '2024-01-01')],
      NOW,
    )

    expect(segments[0].widthPercent).toBeGreaterThanOrEqual(0)
  })

  it('returns nothing for an empty history', () => {
    expect(buildTimelineSegments([], NOW)).toEqual([])
  })

  it('reads dates in UTC, not the reader’s zone', () => {
    const segments = buildTimelineSegments(
      [historyRow(1, 'growth', '2024-01-01', '2024-02-01')],
      NOW,
    )

    expect(segments[0].startMs).toBe(Date.parse('2024-01-01T00:00:00Z'))
  })
})

describe('timelineYearTicks', () => {
  it('marks each year boundary inside the span', () => {
    const segments = buildTimelineSegments(
      [historyRow(1, 'growth', '2021-06-01', '2024-03-01')],
      NOW,
    )

    expect(timelineYearTicks(segments).map((tick) => tick.label)).toEqual([
      '2022',
      '2023',
      '2024',
    ])
  })

  it('places a boundary at its share of the band', () => {
    const segments = buildTimelineSegments(
      [historyRow(1, 'growth', '2023-01-01', '2025-01-01')],
      NOW,
    )
    const [tick] = timelineYearTicks(segments)

    expect(tick.label).toBe('2024')
    expect(tick.offsetPercent).toBeCloseTo(50, 0)
  })

  it('has no ticks for a span inside one year', () => {
    const segments = buildTimelineSegments(
      [historyRow(1, 'growth', '2024-02-01', '2024-06-01')],
      NOW,
    )

    expect(timelineYearTicks(segments)).toEqual([])
  })

  it('has no ticks for an empty history', () => {
    expect(timelineYearTicks([])).toEqual([])
  })
})

describe('timeline zoom', () => {
  it('clamps to the range the band supports', () => {
    expect(clampTimelineZoom(0.1)).toBe(MIN_TIMELINE_ZOOM)
    expect(clampTimelineZoom(99)).toBe(MAX_TIMELINE_ZOOM)
  })

  it('steps up and down the ladder', () => {
    expect(stepTimelineZoom(1, 1)).toBe(2)
    expect(stepTimelineZoom(2, 1)).toBe(4)
    expect(stepTimelineZoom(4, -1)).toBe(2)
  })

  it('stops at each end instead of running past it', () => {
    expect(stepTimelineZoom(MAX_TIMELINE_ZOOM, 1)).toBe(MAX_TIMELINE_ZOOM)
    expect(stepTimelineZoom(MIN_TIMELINE_ZOOM, -1)).toBe(MIN_TIMELINE_ZOOM)
  })
})
