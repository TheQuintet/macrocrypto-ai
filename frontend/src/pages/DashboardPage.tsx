import { ExampleQueryDemo } from '@/components/examples/ExampleQueryDemo'
import { PageIntro } from '@/components/layout/PageIntro'
import { BtcPriceCard } from '@/components/dashboard/price/BtcPriceCard'
import { PriceChangeCard } from '@/components/dashboard/price/PriceChangeCard'
import { RegimeCard } from '@/components/dashboard/regime/RegimeCard'
import { pageCopy } from '@/constants/navigation'
import { PriceChart } from '@/components/dashboard/PriceChart'
import { MacroIndicators } from '@/components/dashboard/MacroIndicators'
import { useMacroIndicatorsQuery } from '@/hooks/useMacroIndicatorsQuery'

export function DashboardPage() {
  const page = pageCopy.dashboard
  const { data: indicators, isLoading, error } = useMacroIndicatorsQuery();

  return (
    <div className="flex min-w-0 flex-col gap-4 sm:gap-6">
      <PageIntro description={page.body} />

      <section className="grid grid-cols-1 gap-3 sm:grid-cols-2 sm:gap-4 lg:grid-cols-3">
        <BtcPriceCard />

        <PriceChangeCard />

        <RegimeCard />
      </section>

      <section className="flex min-w-0 flex-col gap-3">
        <div className="flex flex-col gap-1">
          <h2 className="text-base font-medium">Price</h2>
          <p className="text-sm text-muted-foreground">
            Bitcoin spot with macro overlays
          </p>
        </div>
        <PriceChart />
      </section>
      
      <section className="flex min-w-0 flex-col gap-3">
         <div className="flex flex-col gap-1">
           <h2 className="text-base font-medium">Macroeconomic Indicators</h2>
           <p className="text-sm text-muted-foreground">
              Key economic indicators and their trends
           </p>
         </div>
         <MacroIndicators 
            indicators={indicators || []} 
            isLoading={isLoading}
            error={error}
          />
      </section>

      <section className="flex min-w-0 flex-col gap-3">
        <div className="flex flex-col gap-1">
          <h2 className="text-base font-medium">Query patterns</h2>
          <p className="text-sm text-muted-foreground">
            Scaffold example for TanStack Query fetch + mutation flows.
          </p>
        </div>
        <ExampleQueryDemo />
      </section>

    </div>
  )
}
