import { createContext, useContext } from 'react'

export type AlertListLayout = 'table' | 'card'

export type AlertListLayoutValue = {
  layout: AlertListLayout
  nameLabel: string
  detailLabel: string
}

export const AlertListLayoutContext = createContext<AlertListLayoutValue>({
  layout: 'table',
  nameLabel: 'Alert',
  detailLabel: 'Detail',
})

export function useAlertListLayout() {
  return useContext(AlertListLayoutContext)
}
