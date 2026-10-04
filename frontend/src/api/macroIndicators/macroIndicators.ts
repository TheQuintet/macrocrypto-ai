import { MACRO_INDICATORS_PATH } from '@/constants/apiUrls'
import { apiUrl } from '@/lib/apiConfig'
import type { MacroIndicator } from '@/types/macroIndicators'
import { normalizeMacroIndicatorsFromApi } from '@/lib/macroIndicatorDisplay'
import {
  MACRO_INDICATORS_MOCK_LATENCY_MS,
  delay,
  mockLatestIndicators,
  withDataSource,
} from '@/api/macroIndicators/macroIndicatorsShared'

export { MAIN_INDICATOR_NAMES } from '@/api/macroIndicators/macroIndicatorsShared'

export function macroIndicatorsQueryKey() {
  return ['macroIndicators', 'latest'] as const
}

/** Stand-in latest prints for a frontend-only run, labelled as simulated. */
export async function simulateMacroIndicators(): Promise<MacroIndicator[]> {
  await delay(MACRO_INDICATORS_MOCK_LATENCY_MS)

  return withDataSource(
    mockLatestIndicators.map((indicator) => ({ ...indicator })),
    'simulated',
  )
}

/**
 * Latest indicators from the data service.
 *
 * With no backend configured the app runs on simulated data so it still works
 * standalone. When a backend *is* configured a failed request throws rather
 * than quietly substituting fake prints.
 */
export async function fetchMacroIndicators(): Promise<MacroIndicator[]> {
  const url = apiUrl(MACRO_INDICATORS_PATH)

  if (!url) {
    return simulateMacroIndicators()
  }

  const response = await fetch(url, {
    headers: { Accept: 'application/json' },
  })

  if (!response.ok) {
    throw new Error(`Indicators request failed with ${response.status}`)
  }

  const data = await response.json()
  return withDataSource(
    normalizeMacroIndicatorsFromApi(data.indicators || []),
    'live',
  )
}
