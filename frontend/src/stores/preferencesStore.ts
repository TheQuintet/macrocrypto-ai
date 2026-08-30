import { create } from 'zustand'
import { devtools } from 'zustand/middleware'
import type { CandleInterval } from '@/types/chart'
import type { TimeRange } from '@/types/preferences'

export const TIME_RANGE_OPTIONS: { value: TimeRange; label: string }[] = [
  { value: '30d', label: '30d' },
  { value: '90d', label: '90d' },
  { value: '1y', label: '1y' },
  { value: '5y', label: '5y' },
]

type PreferencesState = {
  timeRange: TimeRange
  setTimeRange: (timeRange: TimeRange) => void
  candleInterval: CandleInterval
  setCandleInterval: (candleInterval: CandleInterval) => void
}

export const usePreferencesStore = create<PreferencesState>()(
  devtools(
    (set) => ({
      timeRange: '30d',
      setTimeRange: (timeRange) =>
        set({ timeRange }, undefined, 'preferences/setTimeRange'),
      candleInterval: '1d',
      setCandleInterval: (candleInterval) =>
        set({ candleInterval }, undefined, 'preferences/setCandleInterval'),
    }),
    { name: 'PreferencesStore' },
  ),
)
