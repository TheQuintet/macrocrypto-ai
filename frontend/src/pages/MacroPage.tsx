import { TimeRangeBadge } from '@/components/time-range-badge'
import { pageCopy } from '@/constants/navigation'

export function MacroPage() {
  const page = pageCopy.macro

  return (
    <main className="flex flex-1 flex-col items-center justify-center gap-4 px-6 py-10 text-center">
      <h1 className="text-3xl font-bold tracking-tight">{page.title}</h1>
      <p className="max-w-md text-muted-foreground">{page.body}</p>
      <TimeRangeBadge />
    </main>
  )
}
