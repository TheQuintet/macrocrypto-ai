import { toast } from 'sonner'
import { ExampleQueryDemo } from '@/components/example-query-demo'
import { TimeRangePicker } from '@/components/time-range-controls'
import { Button } from '@/components/ui/button'
import { pageCopy } from '@/constants/navigation'

export function DashboardPage() {
  const page = pageCopy.dashboard

  return (
    <main className="flex flex-1 flex-col items-center justify-center gap-4 px-6 py-10 text-center">
      <h1 className="text-3xl font-bold tracking-tight">{page.title}</h1>
      <p className="max-w-md text-muted-foreground">{page.body}</p>
      <TimeRangePicker />
      <ExampleQueryDemo />
      <Button
        type="button"
        onClick={() =>
          toast.success('Welcome to MacroCrypto AI', {
            description: 'Your frontend scaffold is ready to build on.',
          })
        }
      >
        Get started
      </Button>
    </main>
  )
}
