import { type NavItemId } from '@/constants/navigation'
import { AlertsPage } from '@/pages/alerts-page'
import { DashboardPage } from '@/pages/dashboard-page'
import { ForecastsPage } from '@/pages/forecasts-page'
import { MacroPage } from '@/pages/macro-page'

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
