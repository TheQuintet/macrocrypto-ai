/** Kinds of alert the "+" button can start. */
export type NewAlertType = 'price' | 'macro'

export type DraftAlert = {
  id: string
  rule: string
  detail: string
}
