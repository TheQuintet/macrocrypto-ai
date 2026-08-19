/** Latest observation from GET /api/v1/indicators. */
export type MacroIndicator = {
  indicator_name: string
  time: string
  current_value: number
  previous_value: number | null
  change_percent: number | null
  trend: '↑' | '↓' | '→'
  source: string
}
