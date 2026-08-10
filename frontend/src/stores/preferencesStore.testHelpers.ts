import { usePreferencesStore } from '@/stores/preferencesStore'
import type { TimeRange } from '@/stores/preferencesStore'

/** Reset shared Zustand state between tests. */
export function resetPreferencesStore(timeRange: TimeRange = '7d'): void {
  usePreferencesStore.setState({ timeRange })
}
