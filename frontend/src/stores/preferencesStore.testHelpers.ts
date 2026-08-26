import { usePreferencesStore } from '@/stores/preferencesStore'
import type { CandleInterval } from '@/types/chart'
import type { TimeRange } from '@/types/preferences'

/** Reset shared Zustand state between tests. */
export function resetPreferencesStore(
  timeRange: TimeRange = '30d',
  candleInterval: CandleInterval = '1d',
): void {
  usePreferencesStore.setState({ timeRange, candleInterval })
}
