import { useCallback, useEffect, useState } from 'react'
import { macroAlertApi } from '@/api/alerts/macroAlerts'
import { draftToWrite, subscriptionToWrite } from '@/lib/alerts/macroEventMapping'
import type {
  MacroAlertDraft,
  MacroSubscription,
} from '@/types/alerts/macroAlert'

/**
 * The user's macro event subscriptions, exactly as the alert service reports
 * them. Every write re-reads the list so the table never shows local guesses.
 */
export function useMacroEvents(userId: string) {
  const [subscriptions, setSubscriptions] = useState<MacroSubscription[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let active = true

    macroAlertApi.getSubscriptions(userId)
      .then((loaded) => {
        if (active) setSubscriptions(loaded)
      })
      .catch(() => {
        if (active) setError('Failed to load macro subscriptions')
      })
      .finally(() => {
        if (active) setIsLoading(false)
      })

    return () => {
      active = false
    }
  }, [userId])

  const fetch = useCallback(async () => {
    setIsLoading(true)
    setError(null)
    try {
      setSubscriptions(await macroAlertApi.getSubscriptions(userId))
    } catch {
      setError('Failed to load macro subscriptions')
    } finally {
      setIsLoading(false)
    }
  }, [userId])

  const subscribe = useCallback(
    async (subscriptionId: string, subscribed: boolean) => {
      const subscription = subscriptions.find((item) => item.id === subscriptionId)
      if (!subscription) return

      await macroAlertApi.updateSubscription(
        userId,
        subscriptionToWrite(subscription, subscribed),
      )
      setSubscriptions(await macroAlertApi.getSubscriptions(userId))
    },
    [subscriptions, userId],
  )

  const applyDraft = useCallback(
    async (draft: MacroAlertDraft) => {
      await macroAlertApi.updateSubscription(userId, draftToWrite(draft))
      setSubscriptions(await macroAlertApi.getSubscriptions(userId))
    },
    [userId],
  )

  return { subscriptions, isLoading, error, fetch, subscribe, applyDraft }
}
