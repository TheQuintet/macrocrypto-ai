import { simulateIncomingNotification } from '@/api/alerts/simulatedNotifications';
import type { NotificationSocketFactory } from '@/types/notificationStream';

/** How soon the simulated stream toasts the first new alert. */
export const MOCK_NOTIFICATION_FIRST_EMIT_MS = 60_000;

/** How often the simulated stream pushes another alert after the first. */
export const MOCK_NOTIFICATION_INTERVAL_MS = 80_000;

/** Simulated connect handshake delay. */
export const MOCK_NOTIFICATION_OPEN_DELAY_MS = 120;

type MockNotificationSocketOptions = {
  userId: string;
  intervalMs?: number;
  openDelayMs?: number;
  firstEmitMs?: number;
  /** When false, the socket opens but never invents alerts (tests / e2e). */
  emitIncoming?: boolean;
};

/**
 * Stands in for the alert-service notification stream until a real SSE/WS
 * route exists. Speaks the same JSON `InAppNotification` wire format.
 */
export function createMockNotificationSocket({
  userId,
  intervalMs = MOCK_NOTIFICATION_INTERVAL_MS,
  openDelayMs = MOCK_NOTIFICATION_OPEN_DELAY_MS,
  firstEmitMs = MOCK_NOTIFICATION_FIRST_EMIT_MS,
  emitIncoming = true,
}: MockNotificationSocketOptions): NotificationSocketFactory {
  return (onEvent) => {
    let isClosed = false;
    let frameTimer: ReturnType<typeof setInterval> | undefined;
    let firstTimer: ReturnType<typeof setTimeout> | undefined;

    const sendFrame = () => {
      if (isClosed) return;

      const notification = simulateIncomingNotification(userId);
      onEvent({
        type: 'message',
        data: JSON.stringify(notification),
      });
    };

    const openTimer = setTimeout(() => {
      if (isClosed) return;

      onEvent({ type: 'open' });
      if (!emitIncoming) return;

      firstTimer = setTimeout(() => {
        sendFrame();
        frameTimer = setInterval(sendFrame, intervalMs);
      }, firstEmitMs);
    }, openDelayMs);

    return {
      close: () => {
        isClosed = true;
        clearTimeout(openTimer);
        if (firstTimer !== undefined) {
          clearTimeout(firstTimer);
          firstTimer = undefined;
        }
        if (frameTimer !== undefined) {
          clearInterval(frameTimer);
          frameTimer = undefined;
        }
      },
    };
  };
}
