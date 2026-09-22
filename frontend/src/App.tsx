import { Navigate, Route, Routes } from 'react-router-dom'
import { AppLayout } from '@/components/layout/AppLayout'
import { routes } from '@/constants/navigation'
import { AlertsPage } from '@/pages/AlertsPage'
import { CalendarPage } from '@/pages/CalendarPage'
import { DashboardPage } from '@/pages/DashboardPage'
import { EconomicNotificationsPage } from '@/pages/EconomicNotificationsPage'
import { ForecastsPage } from '@/pages/ForecastsPage'
import { MacroPage } from '@/pages/MacroPage'

export function App() {
  return (
    <Routes>
      <Route element={<AppLayout />}>
        <Route index element={<DashboardPage />} />
        <Route path={routes.macro} element={<MacroPage />} />
        <Route path={routes.calendar} element={<CalendarPage />} />
        <Route path={routes.economicNotifications} element={<EconomicNotificationsPage />} />
        <Route path={routes.forecasts} element={<ForecastsPage />} />
        <Route path={routes.alerts} element={<AlertsPage />} />
        <Route
          path="*"
          element={<Navigate to={routes.dashboard} replace />}
        />
      </Route>
    </Routes>
  )
}

export default App
