import type {
  AccuracyHistoryPoint,
  AccuracyMetrics,
  AccuracyScore,
  AccuracyScoreKind,
  AccuracyThreshold,
  MarketCondition,
  PredictionAccuracy,
} from '@/types/predictionAccuracy'

/** Placeholder shown wherever an accuracy figure is missing. */
export const ACCURACY_PLACEHOLDER = '--'

const MODEL_FAMILY_LABELS: Record<string, string> = {
  prophet: 'Prophet',
  xgboost: 'XGBoost',
  lightgbm: 'LightGBM',
}

/**
 * Swatch per market, matching the regime stance badges: bull green, bear red,
 * neutral amber. Volatile has no stance there, so it gets its own token.
 */
const MARKET_CONDITION_DOT_CLASSES: Record<MarketCondition, string> = {
  bull: 'bg-positive',
  bear: 'bg-negative',
  volatile: 'bg-market-volatile',
  neutral: 'bg-warning',
}

const MARKET_CONDITION_LABELS: Record<MarketCondition, string> = {
  bull: 'Bull market',
  bear: 'Bear market',
  volatile: 'Volatile',
  neutral: 'Neutral',
}

/** Plain-language names for the service's threshold metric ids. */
const METRIC_LABELS: Record<string, string> = {
  mae_pct: 'Typical miss (% of price)',
  rmse_pct: 'Large-miss error (% of price)',
  mape: 'Average % miss',
  directional_accuracy: 'Direction called right',
}

const SCORE_CAPTIONS: Record<AccuracyScoreKind, string> = {
  directional: 'of forecasts called the direction right',
  price: 'price accuracy (100% minus the average % miss)',
}

/** The threshold metric that grades the same figure as each score kind. */
const SCORE_THRESHOLD_METRIC: Record<AccuracyScoreKind, string> = {
  directional: 'directional_accuracy',
  price: 'mape',
}

function clampPercent(value: number) {
  return Math.min(100, Math.max(0, value))
}

/**
 * The single "N% accurate" figure the card leads with.
 *
 * Direction is what a trader acts on, so it wins when the service reports it.
 * Otherwise the score is 100 − MAPE, and `kind` says so, so the caption can
 * name which figure it is rather than pass one off as the other.
 */
export function accuracyScore(metrics: AccuracyMetrics): AccuracyScore | null {
  if (metrics.directionalAccuracy != null) {
    return {
      kind: 'directional',
      value: clampPercent(metrics.directionalAccuracy),
    }
  }

  if (metrics.mape != null) {
    return { kind: 'price', value: clampPercent(100 - metrics.mape) }
  }

  return null
}

/** The same figure as the headline, for one point of the trend series. */
export function historyScore(
  point: AccuracyHistoryPoint,
  kind: AccuracyScoreKind,
): number | null {
  if (kind === 'directional') {
    return point.directionalAccuracy == null
      ? null
      : clampPercent(point.directionalAccuracy)
  }

  return point.mape == null ? null : clampPercent(100 - point.mape)
}

/** The service's check on the same figure the headline score shows. */
export function scoreThreshold(
  kind: AccuracyScoreKind,
  thresholds: AccuracyThreshold[],
) {
  return thresholds.find((item) => item.metric === SCORE_THRESHOLD_METRIC[kind])
}

/**
 * The service's bound for the headline figure, on the headline's scale —
 * a MAPE ceiling of 10% becomes a 90% floor on the price-accuracy score.
 */
export function scoreTarget(
  kind: AccuracyScoreKind,
  thresholds: AccuracyThreshold[],
): number | null {
  const threshold = scoreThreshold(kind, thresholds)

  if (!threshold) {
    return null
  }

  return kind === 'price'
    ? clampPercent(100 - threshold.threshold)
    : threshold.threshold
}

/** `62%` — whole percent; a decimal place reads as false precision here. */
export function formatAccuracyPercent(value: number | null | undefined) {
  if (value == null || !Number.isFinite(value)) {
    return ACCURACY_PLACEHOLDER
  }

  return `${Math.round(value)}%`
}

/** `1.80%` — error percentages keep two places; they are small numbers. */
export function formatErrorPercent(value: number | null | undefined) {
  if (value == null || !Number.isFinite(value)) {
    return ACCURACY_PLACEHOLDER
  }

  return `${value.toFixed(2)}%`
}

/** `$1,152` — a whole-dollar miss; cents imply precision the metric lacks. */
export function formatUsdMiss(value: number | null | undefined) {
  if (value == null || !Number.isFinite(value)) {
    return ACCURACY_PLACEHOLDER
  }

  return `$${Math.round(value).toLocaleString('en-US')}`
}

export function accuracyScoreCaption(kind: AccuracyScoreKind) {
  return SCORE_CAPTIONS[kind]
}

/** `prophet_fresh` → `Prophet (fresh)`. Unknown names pass through. */
export function formatModelName(modelName: string) {
  const [family, ...strategy] = modelName.split('_')
  const familyLabel = MODEL_FAMILY_LABELS[family.toLowerCase()]

  if (!familyLabel) {
    return modelName
  }

  return strategy.length > 0
    ? `${familyLabel} (${strategy.join(' ')})`
    : familyLabel
}

export function marketConditionLabel(condition: MarketCondition) {
  return MARKET_CONDITION_LABELS[condition]
}

export function marketConditionDotClass(condition: MarketCondition) {
  return MARKET_CONDITION_DOT_CLASSES[condition]
}

export function findThreshold(thresholds: AccuracyThreshold[], metric: string) {
  return thresholds.find((threshold) => threshold.metric === metric)
}

/** How a graded figure stands against its bound, for colouring. */
export type ThresholdTone = 'positive' | 'warning'

const TONE_TEXT_CLASSES: Record<ThresholdTone, string> = {
  positive: 'text-positive',
  warning: 'text-warning',
}

/**
 * Green inside its bound, amber once the service warns. A breach it has not
 * yet warned on gets no tone, and neither does a figure with no bound, since
 * there is nothing to judge it against.
 */
export function thresholdTone(
  threshold: AccuracyThreshold | undefined,
): ThresholdTone | null {
  if (!threshold) {
    return null
  }
  if (threshold.warning) {
    return 'warning'
  }
  return threshold.breached ? null : 'positive'
}

export function thresholdToneClass(threshold: AccuracyThreshold | undefined) {
  const tone = thresholdTone(threshold)
  return tone ? TONE_TEXT_CLASSES[tone] : ''
}

export function accuracyMetricLabel(metric: string) {
  return METRIC_LABELS[metric] ?? metric
}

/**
 * A check's current value, in the same form the rest of the card uses:
 * whole percent for direction, two places for the small error percentages.
 */
export function formatThresholdValue(threshold: AccuracyThreshold) {
  return threshold.metric === 'directional_accuracy'
    ? formatAccuracyPercent(threshold.value)
    : formatErrorPercent(threshold.value)
}

/** `Must stay below 10%` / `Must stay above 55%`. */
export function formatThresholdRule(threshold: AccuracyThreshold) {
  const side = threshold.breachDirection === 'above' ? 'below' : 'above'
  return `Must stay ${side} ${formatAccuracyPercent(threshold.threshold)}`
}

function pluralDays(days: number) {
  return `${days} ${days === 1 ? 'day' : 'days'}`
}

function pluralMetrics(count: number) {
  return `${count} ${count === 1 ? 'metric' : 'metrics'}`
}

type AccuracyWarningSource = Pick<
  PredictionAccuracy,
  'thresholds' | 'warning' | 'warningCount' | 'warningThresholdDays'
>

/**
 * One sentence per metric the service is warning about, e.g.
 * `Average % miss has been above 10% for 4 days in a row.`
 *
 * Only `warning` counts: a single-day breach is noise the service itself
 * waits out before flagging. The entry-wide flag can cover metrics that are
 * missing from `thresholds` (the service drops the %-of-price checks when it
 * has no mean price), so any it cannot name are still reported.
 */
export function accuracyWarningMessages({
  thresholds,
  warning,
  warningCount,
  warningThresholdDays,
}: AccuracyWarningSource) {
  const named = thresholds
    .filter((threshold) => threshold.warning)
    .map((threshold) => {
      const side = threshold.breachDirection === 'above' ? 'above' : 'below'
      return `${accuracyMetricLabel(threshold.metric)} has been ${side} ${formatAccuracyPercent(threshold.threshold)} for ${pluralDays(threshold.consecutiveDays)} in a row.`
    })

  if (!warning) {
    return named
  }

  const unnamed = Math.max(warningCount, 1) - named.length
  if (unnamed <= 0) {
    return named
  }

  const streak = `for ${warningThresholdDays}+ days in a row`
  return [
    ...named,
    named.length > 0
      ? `The service is also flagging ${pluralMetrics(unnamed)} ${streak}.`
      : `The service has flagged ${pluralMetrics(unnamed)} outside ${unnamed === 1 ? 'its bound' : 'their bounds'} ${streak}.`,
  ]
}

/** `Last 30 days`. */
export function formatAccuracyPeriod(days: number) {
  return `Last ${pluralDays(days)}`
}

/** `720`. */
export function formatSampleCount(samples: number) {
  return samples.toLocaleString('en-US')
}

/** `14 Sep 2026` in the reader's timezone. */
export function formatAccuracyDate(iso: string | null | undefined) {
  if (!iso) {
    return ACCURACY_PLACEHOLDER
  }

  const parsed = new Date(iso)
  if (Number.isNaN(parsed.getTime())) {
    return ACCURACY_PLACEHOLDER
  }

  return parsed.toLocaleDateString('en-GB', {
    day: 'numeric',
    month: 'short',
    year: 'numeric',
  })
}

/** Short axis/tooltip date, e.g. `14 Sep`. */
export function formatAccuracyDay(timeMs: number) {
  return new Date(timeMs).toLocaleDateString('en-GB', {
    day: 'numeric',
    month: 'short',
  })
}
