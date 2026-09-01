import { routes } from '@/constants/navigation'
import type { InAppNotification } from '@/types/alerts/notifications'

/**
 * In-app destination for a notification click.
 * Price alerts open the chart (dashboard); other types go to their page.
 */
export function notificationActionPath(
  notification: InAppNotification,
): string {
  switch (notification.notification_type) {
    case 'price_alert':
      return routes.dashboard
    case 'prediction_alert':
    case 'confidence_alert':
      return routes.forecasts
    case 'macro_alert':
      return routes.macro
    default:
      return routes.dashboard
  }
}
