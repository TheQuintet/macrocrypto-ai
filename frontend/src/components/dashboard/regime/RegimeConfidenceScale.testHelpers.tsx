import { render, screen } from '@testing-library/react'
import { expect } from 'vitest'
import { RegimeConfidenceScale } from '@/components/dashboard/regime/RegimeConfidenceScale'
import {
  CONFIDENCE_BAND_ORDER,
  formatConfidenceBand,
  formatConfidenceBandRange,
} from '@/lib/regimeDisplay'

export function renderRegimeConfidenceScale() {
  return render(<RegimeConfidenceScale />)
}

export function expectConfidenceScaleKey() {
  for (const band of CONFIDENCE_BAND_ORDER) {
    expect(
      screen.getByText(
        `${formatConfidenceBand(band)} ${formatConfidenceBandRange(band)}`,
      ),
    ).toBeInTheDocument()
  }
}
