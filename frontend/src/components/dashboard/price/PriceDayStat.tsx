type PriceDayStatProps = {
  label: string
  value: string
}

/** One label/value pair in the 24h session row. */
export function PriceDayStat({ label, value }: PriceDayStatProps) {
  return (
    <div className="flex min-w-0 items-baseline gap-1">
      <dt>{label}</dt>
      <dd className="font-medium tabular-nums text-foreground">{value}</dd>
    </div>
  )
}
