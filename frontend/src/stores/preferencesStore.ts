import { create } from 'zustand'
import { devtools } from 'zustand/middleware'

export type TimeRange = '24h' | '7d' | '30d' | '90d'

export const TIME_RANGE_OPTIONS: { value: TimeRange; label: string }[] = [
  { value: '24h', label: '24h' },
  { value: '7d', label: '7d' },
  { value: '30d', label: '30d' },
  { value: '90d', label: '90d' },
]

type PreferencesState = {
  timeRange: TimeRange
  setTimeRange: (timeRange: TimeRange) => void
}

export const usePreferencesStore = create<PreferencesState>()(
  devtools(
    (set) => ({
      timeRange: '7d',
      setTimeRange: (timeRange) =>
        set({ timeRange }, undefined, 'preferences/setTimeRange'),
    }),
    { name: 'PreferencesStore' },
  ),
)
