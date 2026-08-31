import { useNotificationStreamStore } from '@/stores/notificationStreamStore'
import type { NotificationStreamStatus } from '@/types/notificationStream'

export function resetNotificationStreamStore(
  status: NotificationStreamStatus = 'connecting',
): void {
  useNotificationStreamStore.setState({ status, reconnectAttempts: 0 })
}
