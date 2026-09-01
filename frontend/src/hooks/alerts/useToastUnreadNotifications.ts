import { useEffect, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  NOTIFICATION_TOAST_DURATION_MS,
  showToast,
} from '@/components/alerts/shared/ToastNotification'
import { useMarkNotificationReadMutation } from '@/hooks/alerts/useMarkNotificationReadMutation'
import { useNotificationsQuery } from '@/hooks/alerts/useNotificationsQuery'
import { formatNotificationToast } from '@/lib/alerts/formatNotificationToast'
import { notificationActionPath } from '@/lib/alerts/notificationActionPath'
import { unreadNotificationsToToast } from '@/lib/alerts/unreadNotificationsToToast'

/**
 * On first inbox load, toasts every unread notification (oldest first so the
 * newest sits on top of the overlapping pile). Later arrivals come from the
 * live stream. Hover the pile to expand and read them all.
 */
export function useToastUnreadNotifications(userId: string) {
  const { data, isSuccess } = useNotificationsQuery(userId)
  const navigate = useNavigate()
  const markAsRead = useMarkNotificationReadMutation(userId)
  const hasPrimed = useRef(false)

  useEffect(() => {
    if (hasPrimed.current || !isSuccess || !data) return

    hasPrimed.current = true
    const markRead = markAsRead.mutate

    for (const incoming of unreadNotificationsToToast(data.notifications)) {
      const toastCopy = formatNotificationToast(incoming)
      showToast.notification(toastCopy.title, toastCopy.description, {
        id: incoming.id,
        notificationType: incoming.notification_type,
        duration: NOTIFICATION_TOAST_DURATION_MS,
        onClick: () => {
          if (!incoming.read) {
            markRead(incoming.id)
          }
          navigate(notificationActionPath(incoming))
        },
      })
    }
  }, [data, isSuccess, markAsRead.mutate, navigate])
}
