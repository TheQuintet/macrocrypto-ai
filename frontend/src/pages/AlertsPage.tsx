import { pageCopy } from '@/constants/navigation'

export function AlertsPage() {
  const page = pageCopy.alerts

  return (
    <main className="flex flex-1 flex-col items-center justify-center gap-4 px-6 py-10 text-center">
      <h1 className="text-3xl font-bold tracking-tight">{page.title}</h1>
      <p className="max-w-md text-muted-foreground">{page.body}</p>
    </main>
  )
}
