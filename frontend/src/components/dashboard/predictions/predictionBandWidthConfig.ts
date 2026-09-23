import type { PredictionBandWidth } from '@/types/predictions'

export type PredictionBandWidthConfig = {
  label: string
  /** What a band this wide says about the forecast, in plain terms. */
  description: string
  className: string
  dot: string
}

/**
 * Colour-coded reliability read on the band, in the same shape as the event
 * impact badge so the two surfaces read as one system.
 */
const bandWidthConfig: Record<PredictionBandWidth, PredictionBandWidthConfig> =
  {
    narrow: {
      label: 'Narrow',
      description: 'Tight range — the model is confident about where price lands',
      className: 'bg-positive/15 text-positive',
      dot: 'bg-positive',
    },
    medium: {
      label: 'Medium',
      description: 'Moderate range — treat the midpoint as indicative',
      className: 'bg-warning/15 text-warning',
      dot: 'bg-warning',
    },
    wide: {
      label: 'Wide',
      description: 'Broad range — low certainty about where price lands',
      className: 'bg-negative/15 text-negative',
      dot: 'bg-negative',
    },
  }

export function getPredictionBandWidthConfig(width: PredictionBandWidth) {
  return bandWidthConfig[width]
}
