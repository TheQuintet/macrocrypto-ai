import type {
  AccuracyHistoryPoint,
  AccuracyMetrics,
  AccuracyScore,
  AccuracyScoreKind,
  AccuracyThreshold,
  AccuracyTrendRow,
  MarketCondition,
  MarketGrade,
  PredictionAccuracy,
  PredictionAccuracyPoint,
  TrendTarget,
} from '@/types/predictionAccuracy'
import type { PredictionHorizon } from '@/types/predictions'

/** Placeholder shown wherever an accuracy figure is missing. */
export const ACCURACY_PLACEHOLDER = '--'

const MODEL_FAMILY_LABELS: Record<string, string> = {
  prophet: 'Prophet',
  xgboost: 'XGBoost',
  lightgbm: 'LightGBM',
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

/** What the headline figure is, named above it. */
const SCORE_LABELS: Record<AccuracyScoreKind, string> = {
  directional: 'Direction accuracy',
  price: 'Price accuracy',
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

export function accuracyScoreLabel(kind: AccuracyScoreKind) {
  return SCORE_LABELS[kind]
}

/**
 * The headline in plain words. Price accuracy is 100 − MAPE, so it is put
 * as how close forecasts landed, never as "right N% of the time", which only
 * a direction score can claim.
 */
export function accuracyScoreExplanation(
  kind: AccuracyScoreKind,
  metrics: AccuracyMetrics,
) {
  if (kind === 'directional') {
    return `Called the direction right ${formatAccuracyPercent(metrics.directionalAccuracy)} of the time.`
  }

  const usd =
    metrics.mae == null ? '' : ` (about ${formatUsdMiss(metrics.mae)})`
  return `Forecasts were within ${formatErrorPercent(metrics.mape)} of the real price on average${usd}.`
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

const TREND_CAPTIONS: Record<AccuracyScoreKind, string> = {
  directional: 'Direction called right, % of forecasts, day by day',
  price: 'Price accuracy (100% minus the average % miss), day by day',
}

/**
 * The one figure every trend line plots. Lines on a shared axis must mean
 * the same thing, so direction is used only when every horizon reports it;
 * if either lacks it, both plot price accuracy.
 */
export function trendScoreKind(
  accuracies: PredictionAccuracy[],
): AccuracyScoreKind {
  return accuracies.length > 0 &&
    accuracies.every((accuracy) => accuracy.metrics.directionalAccuracy != null)
    ? 'directional'
    : 'price'
}

/**
 * Each horizon's history merged on time, one row per moment either was
 * scored. A horizon with nothing at a moment leaves a gap there.
 */
export function buildAccuracyTrend(
  accuracies: PredictionAccuracy[],
  kind: AccuracyScoreKind,
): AccuracyTrendRow[] {
  const rows = new Map<number, AccuracyTrendRow>()

  for (const accuracy of accuracies) {
    for (const point of accuracy.history) {
      const row = rows.get(point.timeMs) ?? { timeMs: point.timeMs }
      rows.set(point.timeMs, {
        ...row,
        [accuracy.horizon]: historyScore(point, kind),
      })
    }
  }

  return [...rows.values()].sort((a, b) => a.timeMs - b.timeMs)
}

export function accuracyTrendCaption(kind: AccuracyScoreKind) {
  return TREND_CAPTIONS[kind]
}

/** `24h forecasts` — the trend's name for one horizon's line. */
export function accuracyTrendLineLabel(horizon: PredictionHorizon) {
  return `${horizon} forecasts`
}

type TrendLineStyle = {
  stroke: string
  swatchClass: string
}

/**
 * Each horizon keeps its own colour whatever the chart toggle says, since
 * the trend always shows both. Teal and violet: apart in hue and lightness,
 * and neither is a grade colour, so a line never reads as "good" or "bad".
 */
const TREND_LINE_STYLES: Record<PredictionHorizon, TrendLineStyle> = {
  '24h': { stroke: 'var(--chart-1)', swatchClass: 'bg-chart-1' },
  '7d': { stroke: 'var(--indicator-gdp)', swatchClass: 'bg-indicator-gdp' },
}

export function trendLineStyle(horizon: PredictionHorizon): TrendLineStyle {
  return TREND_LINE_STYLES[horizon]
}

/**
 * The service's bound for each horizon on the plotted scale, merged where
 * they agree, so one dashed line stands for both when the bound is shared.
 */
export function trendTargets(
  accuracies: PredictionAccuracy[],
  kind: AccuracyScoreKind,
): TrendTarget[] {
  const targets: TrendTarget[] = []

  for (const accuracy of accuracies) {
    const value = scoreTarget(kind, accuracy.thresholds)
    if (value == null) {
      continue
    }
    const same = targets.find((target) => target.value === value)
    if (same) {
      same.horizons.push(accuracy.horizon)
    } else {
      targets.push({ value, horizons: [accuracy.horizon] })
    }
  }

  return targets
}

/** `Service target 90% (24h & 7d)`. */
export function formatTrendTarget(target: TrendTarget) {
  return `Service target ${formatAccuracyPercent(target.value)} (${target.horizons.join(' & ')})`
}

/**
 * Why a horizon's line is missing from the trend, or null while it is drawn
 * (or still loading, when it will be).
 */
export function accuracyTrendGapNote(
  horizon: PredictionHorizon,
  accuracy: PredictionAccuracy | null | undefined,
  error: Error | null,
) {
  if (error) {
    return `The ${horizon} line is unavailable: ${error.message}`
  }
  if (accuracy === null) {
    return `No ${horizon} forecasts have been scored yet, so there is no ${horizon} line.`
  }
  return null
}

const MARKET_GRADE_TEXT_CLASSES: Record<MarketGrade, string> = {
  good: 'text-positive',
  medium: 'text-warning',
  poor: 'text-negative',
}

const MARKET_GRADE_BAR_CLASSES: Record<MarketGrade, string> = {
  good: 'bg-positive',
  medium: 'bg-warning',
  poor: 'bg-negative',
}

/** A market's price accuracy, on the same 100 − MAPE scale as the headline. */
export function marketAccuracy(mape: number | null): number | null {
  return mape == null ? null : clampPercent(100 - mape)
}

/**
 * Grades a market against two facts the service reports, so no cut-off is
 * invented here: red once its miss is beyond the service's MAPE bound,
 * yellow when it misses more than the model does overall, green otherwise.
 * Without a bound it is never red; with neither fact it is not graded.
 */
export function marketGrade(
  mape: number | null,
  overallMape: number | null,
  mapeThreshold: AccuracyThreshold | undefined,
): MarketGrade | null {
  if (mape == null) {
    return null
  }

  if (mapeThreshold) {
    const beyond =
      mapeThreshold.breachDirection === 'above'
        ? mape > mapeThreshold.threshold
        : mape < mapeThreshold.threshold
    if (beyond) {
      return 'poor'
    }
  }

  if (overallMape == null) {
    return mapeThreshold ? 'good' : null
  }

  return mape <= overallMape ? 'good' : 'medium'
}

export function marketGradeTextClass(grade: MarketGrade | null) {
  return grade ? MARKET_GRADE_TEXT_CLASSES[grade] : ''
}

export function marketGradeBarClass(grade: MarketGrade | null) {
  return grade ? MARKET_GRADE_BAR_CLASSES[grade] : 'bg-muted-foreground'
}

/** One line explaining the market colours, naming the bound when there is one. */
export function marketGradeLegend(mapeThreshold: AccuracyThreshold | undefined) {
  const relative =
    'Green: as accurate as the model overall or better. Yellow: less accurate.'

  return mapeThreshold
    ? `${relative} Red: misses beyond the service's ${formatAccuracyPercent(mapeThreshold.threshold)} bound.`
    : relative
}

/** `$64,101` — a whole-dollar BTC price. */
export function formatUsdPrice(value: number) {
  return `$${Math.round(value).toLocaleString('en-US')}`
}

/**
 * How far the forecast landed from the real price, signed from the
 * forecast's side: `+$220 (+0.34%)` means it came in above.
 */
export function formatPriceGap(predicted: number, actual: number) {
  const gap = predicted - actual
  const sign = gap > 0 ? '+' : gap < 0 ? '-' : ''
  const usd = `${sign}$${Math.abs(Math.round(gap)).toLocaleString('en-US')}`

  if (actual === 0) {
    return usd
  }

  return `${usd} (${sign}${Math.abs((gap / actual) * 100).toFixed(2)}%)`
}

/** Tooltip moment for a scored forecast, e.g. `14 Sep, 06:00`. */
export function formatAccuracyMoment(timeMs: number) {
  return new Date(timeMs).toLocaleString('en-GB', {
    day: 'numeric',
    month: 'short',
    hour: '2-digit',
    minute: '2-digit',
  })
}

/** Zoom-in steps on the comparison; each halves the span shown. */
const COMPARISON_ZOOM_MAX = 4

/** Never zoom in past this many forecasts, or the lines stop reading as lines. */
const COMPARISON_MIN_ZOOM_POINTS = 5

function zoomedSince(points: PredictionAccuracyPoint[], level: number) {
  const first = points[0].timeMs
  const last = points[points.length - 1].timeMs
  return last - (last - first) / 2 ** level
}

/**
 * The most recent stretch at a zoom level: level 0 is every point, and each
 * step in shows the latest half of the span before it. No panning, so
 * zooming in always means "closer to now".
 */
export function comparisonZoomPoints(
  points: PredictionAccuracyPoint[],
  level: number,
) {
  if (points.length === 0 || level <= 0) {
    return points
  }

  const since = zoomedSince(points, level)
  return points.filter((point) => point.timeMs >= since)
}

/** The deepest zoom that still shows a handful of forecasts. */
export function comparisonMaxZoom(points: PredictionAccuracyPoint[]) {
  let level = 0
  while (
    level < COMPARISON_ZOOM_MAX &&
    comparisonZoomPoints(points, level + 1).length >= COMPARISON_MIN_ZOOM_POINTS
  ) {
    level += 1
  }
  return level
}

/**
 * `Showing the last 11 days` — whole days, at least one. Each point stands
 * for one step of time, so the span runs one step past the first point:
 * 90 daily forecasts cover 90 days, not the 89 between first and last.
 */
export function formatComparisonSpan(points: PredictionAccuracyPoint[]) {
  if (points.length < 2) {
    return 'Showing one forecast'
  }

  const dayMs = 24 * 60 * 60 * 1000
  const last = points[points.length - 1].timeMs
  const step = last - points[points.length - 2].timeMs
  const days = Math.max(1, Math.round((last - points[0].timeMs + step) / dayMs))
  return `Showing the last ${days} ${days === 1 ? 'day' : 'days'}`
}
