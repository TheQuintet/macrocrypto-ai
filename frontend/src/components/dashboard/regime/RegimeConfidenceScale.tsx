import {
  CONFIDENCE_BAND_ORDER,
  confidenceBandTone,
  formatConfidenceBand,
  formatConfidenceBandRange,
} from '@/lib/regimeDisplay'
import { cn } from '@/lib/utils'

/** Always-visible key so low / moderate / high colours can be read at a glance. */
export function RegimeConfidenceScale() {
  return (
    <ul className="m-0 flex list-none flex-wrap gap-x-3 gap-y-1 p-0 text-[10px] leading-none">
      {CONFIDENCE_BAND_ORDER.map((band) => (
        <li
          key={band}
          className={cn('font-medium', confidenceBandTone(band).toneClass)}
        >
          {`${formatConfidenceBand(band)} ${formatConfidenceBandRange(band)}`}
        </li>
      ))}
    </ul>
  )
}
