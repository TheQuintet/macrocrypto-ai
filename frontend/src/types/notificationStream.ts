/**
 * Transport state of the live notification connection.
 * `unavailable` means no stream is configured — REST polling carries updates.
 */
export type NotificationStreamStatus =
  | 'connecting'
  | 'connected'
  | 'disconnected'
  | 'unavailable'

export type NotificationSocketEvent =
  | { type: 'open' }
  | { type: 'message'; data: string }
  | { type: 'close' }
  | { type: 'error' }

export type NotificationSocketHandle = {
  close: () => void
}

/** Opens a transport and pushes its events into `onEvent`. */
export type NotificationSocketFactory = (
  onEvent: (event: NotificationSocketEvent) => void,
) => NotificationSocketHandle
