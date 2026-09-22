type PredictionTooltipRowProps = {
  label: string
  value: string
}

/** One label/value line inside the forecast tooltip. */
export function PredictionTooltipRow({
  label,
  value,
}: PredictionTooltipRowProps) {
  return (
    <div className="flex items-center justify-between gap-4">
      <span className="text-muted-foreground">{label}</span>
      <span className="font-mono tabular-nums">{value}</span>
    </div>
  )
}
