import type { PredictionBandWidth } from '@/types/predictions'

export type PredictionBandWidthConfig = {
  label: string
  /** How far price may range around the forecast line, in plain terms. */
  description: string
  className: string
  dot: string
}

/**
 * Colour-coded read on how wide the band runs, in the same shape as the event
 * impact badge so the two surfaces read as one system.
 *
 * The copy describes the spread only. Width follows the coverage level as much
 * as the model — a 95% band is wider than a 70% one from the same forecast —
 * so it is not a verdict on how confident the model is.
 */
const bandWidthConfig: Record<PredictionBandWidth, PredictionBandWidthConfig> =
  {
    narrow: {
      label: 'Narrow',
      description: 'Tight band — price is projected to stay close to the line',
      className: 'bg-positive/15 text-positive',
      dot: 'bg-positive',
    },
    medium: {
      label: 'Medium',
      description: 'Moderate band — allow for some spread around the line',
      className: 'bg-warning/15 text-warning',
      dot: 'bg-warning',
    },
    wide: {
      label: 'Wide',
      description: 'Broad band — price could land well away from the line',
      className: 'bg-negative/15 text-negative',
      dot: 'bg-negative',
    },
  }

export function getPredictionBandWidthConfig(width: PredictionBandWidth) {
  return bandWidthConfig[width]
}
