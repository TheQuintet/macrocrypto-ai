import { type NavItemId } from '@/constants/navigation'
import { AlertsPage } from '@/pages/AlertsPage'
import { DashboardPage } from '@/pages/DashboardPage'
import { ForecastsPage } from '@/pages/ForecastsPage'
import { MacroPage } from '@/pages/MacroPage'

export function PageContent({ activeNav }: { activeNav: NavItemId }) {
  switch (activeNav) {
    case 'dashboard':
      return <DashboardPage />
    case 'macro':
      return <MacroPage />
    case 'forecasts':
      return <ForecastsPage />
    case 'alerts':
      return <AlertsPage />
  }
}
