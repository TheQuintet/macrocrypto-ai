import { usePreferencesStore } from '@/stores/preferences-store'
import type { TimeRange } from '@/stores/preferences-store'

/** Reset shared Zustand state between tests. */
export function resetPreferencesStore(timeRange: TimeRange = '7d'): void {
  usePreferencesStore.setState({ timeRange })
}
