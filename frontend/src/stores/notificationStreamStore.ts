import { create } from 'zustand'
import { devtools } from 'zustand/middleware'
import type { NotificationStreamStatus } from '@/types/notificationStream'

type NotificationStreamState = {
  status: NotificationStreamStatus
  reconnectAttempts: number
  setStatus: (status: NotificationStreamStatus) => void
  setReconnectAttempts: (reconnectAttempts: number) => void
}

/** Live-connection state: transport status, not server data. */
export const useNotificationStreamStore = create<NotificationStreamState>()(
  devtools(
    (set) => ({
      status: 'connecting',
      reconnectAttempts: 0,
      setStatus: (status) =>
        set({ status }, undefined, 'notificationStream/setStatus'),
      setReconnectAttempts: (reconnectAttempts) =>
        set(
          { reconnectAttempts },
          undefined,
          'notificationStream/setReconnectAttempts',
        ),
    }),
    { name: 'NotificationStreamStore' },
  ),
)
