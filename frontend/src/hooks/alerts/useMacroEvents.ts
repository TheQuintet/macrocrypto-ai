import { useCallback, useEffect, useState } from 'react'
import { macroAlertApi } from '@/api/alerts/macroAlerts'
import type {
  EventTiming,
  EventType,
  MacroAlertDraft,
  MacroEvent,
  MacroSubscription,
} from '@/types/alerts/macroAlert'

export type MacroEventSubscription = {
  timing: EventTiming
  oneTime: boolean
}

type MacroEventsSnapshot = {
  events: MacroEvent[]
  subscriptions: Map<EventType, MacroEventSubscription>
}

function toSubscriptionMap(
  subscriptions: MacroSubscription[],
): Map<EventType, MacroEventSubscription> {
  return new Map(
    subscriptions.map((sub) => [
      sub.event_type,
      { timing: sub.timing ?? '1D', oneTime: sub.one_time ?? true },
    ]),
  )
}

async function loadMacroEvents(): Promise<MacroEventsSnapshot> {
  const [events, subscriptions] = await Promise.all([
    macroAlertApi.getUpcomingEvents(),
    macroAlertApi.getSubscriptions(),
  ])
  return { events, subscriptions: toSubscriptionMap(subscriptions) }
}

/** Upcoming macro events plus this user's subscriptions, shared by page and table. */
export function useMacroEvents(userId: string) {
  const [events, setEvents] = useState<MacroEvent[]>([])
  const [subscriptions, setSubscriptions] = useState<Map<EventType, MacroEventSubscription>>(
    new Map(),
  )
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const applySnapshot = useCallback((snapshot: MacroEventsSnapshot) => {
    setEvents(snapshot.events)
    setSubscriptions(snapshot.subscriptions)
  }, [])

  useEffect(() => {
    let active = true

    loadMacroEvents()
      .then((snapshot) => {
        if (active) applySnapshot(snapshot)
      })
      .catch(() => {
        if (active) setError('Failed to load events')
      })
      .finally(() => {
        if (active) setIsLoading(false)
      })

    return () => {
      active = false
    }
  }, [applySnapshot])

  const fetch = useCallback(async () => {
    setIsLoading(true)
    setError(null)
    try {
      applySnapshot(await loadMacroEvents())
    } catch {
      setError('Failed to load events')
    } finally {
      setIsLoading(false)
    }
  }, [applySnapshot])

  const subscribe = useCallback(
    async (eventId: string, subscribed: boolean) => {
      const event = events.find((item) => item.id === eventId)
      if (!event) return

      await macroAlertApi.updateSubscription(userId, event.event_type, subscribed)
      setEvents((prev) =>
        prev.map((item) => (item.id === eventId ? { ...item, subscribed } : item)),
      )
    },
    [events, userId],
  )

  /** Subscribe to the drafted event and remember how it should notify. */
  const applyDraft = useCallback(
    async (draft: MacroAlertDraft) => {
      const event = events.find((item) => item.event_type === draft.event_type)
      if (!event) return

      await macroAlertApi.updateSubscription(
        userId,
        draft.event_type,
        true,
        draft.one_time,
      )
      setSubscriptions((prev) =>
        new Map(prev).set(draft.event_type, {
          timing: draft.timing,
          oneTime: draft.one_time,
        }),
      )
      setEvents((prev) =>
        prev.map((item) =>
          item.event_type === draft.event_type ? { ...item, subscribed: true } : item,
        ),
      )
    },
    [events, userId],
  )

  return { events, subscriptions, isLoading, error, fetch, subscribe, applyDraft }
}
