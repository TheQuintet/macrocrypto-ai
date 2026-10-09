import { useQueryClient } from '@tanstack/react-query'
import { useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  notificationsQueryKey,
  unreadNotificationCountQueryKey,
} from '@/api/alerts/notifications'
import {
  NOTIFICATION_TOAST_DURATION_MS,
  showToast,
} from '@/components/alerts/shared/ToastNotification'
import { useMarkNotificationReadMutation } from '@/hooks/alerts/useMarkNotificationReadMutation'
import { formatNotificationToast } from '@/lib/alerts/formatNotificationToast'
import {
  listContainsNotification,
  mergeIncomingNotification,
  unreadCountAfterIncoming,
} from '@/lib/alerts/mergeIncomingNotification'
import { notificationActionPath } from '@/lib/alerts/notificationActionPath'
import { createNotificationSocket } from '@/lib/notificationSocket'
import {
  notificationReconnectDelayMs,
  parseNotificationStreamMessage,
} from '@/lib/notificationStream'
import { useNotificationStreamStore } from '@/stores/notificationStreamStore'
import type { NotificationResponse } from '@/types/alerts/notifications'
import type {
  NotificationSocketFactory,
  NotificationSocketHandle,
} from '@/types/notificationStream'

type UseNotificationStreamOptions = {
  socketFactory?: NotificationSocketFactory | null
}

/**
 * Keeps the inbox live off SSE/WebSocket, reconnecting with backoff when
 * the connection drops. Frames are written into the TanStack Query cache.
 */
export function useNotificationStream(
  userId: string,
  { socketFactory }: UseNotificationStreamOptions = {},
) {
  const queryClient = useQueryClient()
  const navigate = useNavigate()
  const markAsRead = useMarkNotificationReadMutation(userId)
  const status = useNotificationStreamStore((state) => state.status)
  const setStatus = useNotificationStreamStore((state) => state.setStatus)
  const reconnectAttempts = useNotificationStreamStore(
    (state) => state.reconnectAttempts,
  )
  const setReconnectAttempts = useNotificationStreamStore(
    (state) => state.setReconnectAttempts,
  )

  useEffect(() => {
    if (!userId) {
      setStatus('unavailable')
      return
    }

    const factory =
      socketFactory === undefined
        ? createNotificationSocket(userId)
        : socketFactory

    if (!factory) {
      setStatus('unavailable')
      return
    }

    const connect = factory
    const markRead = markAsRead.mutate

    let handle: NotificationSocketHandle | undefined
    let reconnectTimer: ReturnType<typeof setTimeout> | undefined
    let attempt = 0
    let isCancelled = false

    const applyIncoming = (data: string) => {
      const incoming = parseNotificationStreamMessage(data)
      if (!incoming) return

      const listKey = notificationsQueryKey(userId)
      const current = queryClient.getQueryData<NotificationResponse>(listKey)
      const alreadyKnown = listContainsNotification(current, incoming.id)

      if (current) {
        queryClient.setQueryData(
          listKey,
          mergeIncomingNotification(current, incoming),
        )
      } else {
        void queryClient.invalidateQueries({ queryKey: listKey })
      }
      queryClient.setQueryData<{ count: number }>(
        unreadNotificationCountQueryKey(userId),
        (countState) => ({
          count: unreadCountAfterIncoming(
            countState?.count,
            incoming,
            alreadyKnown,
          ),
        }),
      )

      if (!alreadyKnown && !incoming.read) {
        const toastCopy = formatNotificationToast(incoming)
        showToast.notification(toastCopy.title, toastCopy.description, {
          id: incoming.id,
          notificationType: incoming.notification_type,
          duration: NOTIFICATION_TOAST_DURATION_MS,
          onClick: () => {
            if (!incoming.read) {
              markRead(incoming)
            }
            navigate(notificationActionPath(incoming))
          },
        })
      }
    }

    const scheduleReconnect = () => {
      if (isCancelled) return

      attempt += 1
      setReconnectAttempts(attempt)
      setStatus('disconnected')
      reconnectTimer = setTimeout(open, notificationReconnectDelayMs(attempt))
    }

    function open() {
      if (isCancelled) return

      setStatus(attempt === 0 ? 'connecting' : 'disconnected')

      handle = connect((event) => {
        if (isCancelled) return

        if (event.type === 'open') {
          attempt = 0
          setReconnectAttempts(0)
          setStatus('connected')
          return
        }

        if (event.type === 'message') {
          applyIncoming(event.data)
          return
        }

        handle?.close()
        handle = undefined
        scheduleReconnect()
      })
    }

    open()

    return () => {
      isCancelled = true
      clearTimeout(reconnectTimer)
      handle?.close()
    }
  }, [
    markAsRead.mutate,
    navigate,
    queryClient,
    socketFactory,
    userId,
    setStatus,
    setReconnectAttempts,
  ])

  return { status, reconnectAttempts }
}
