/** Kinds of alert the "+" button can start. */
export type NewAlertType = 'price' | 'macro' | 'prediction'

// Re-export prediction types from the alerts subdirectory
export * from './alerts/predictionAlert'
