/** Kinds of alert the "+" button can start. */
export type NewAlertType = 'price' | 'macro' | 'prediction';

export type DraftAlert = {
  id: string;
  rule: string;
  detail: string;
};

// Re-export prediction types from the alerts subdirectory
export * from './alerts/predictionAlert';
