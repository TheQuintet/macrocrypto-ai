/**
 * The `confidence` a batch carries is the coverage level its band was
 * computed at: how often price is expected to land inside the band. It is
 * chosen by the caller, not earned by the model, so nothing here names it
 * high or low — a 95% band is wider than a 70% one, not better.
 */

export function clampPredictionConfidence(confidence: number) {
  if (!Number.isFinite(confidence)) {
    return 0
  }

  return Math.min(1, Math.max(0, confidence))
}

export function predictionConfidencePercent(confidence: number) {
  return Math.round(clampPredictionConfidence(confidence) * 100)
}

/** `0.85` -> `85% range`. */
export function formatPredictionCoverage(confidence: number) {
  return `${predictionConfidencePercent(confidence)}% range`
}

/** What the coverage level promises, in plain terms. */
export function describePredictionCoverage(confidence: number) {
  return `Price expected inside the band ${predictionConfidencePercent(confidence)}% of the time`
}
