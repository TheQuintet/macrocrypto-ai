import { render, screen } from '@testing-library/react'
import type { UserEvent } from '@testing-library/user-event'
import { expect } from 'vitest'
import { IndicatorHistoryFilter } from '@/components/dashboard/indicators/IndicatorHistoryFilter'
import type { IndicatorHistoryFilter as IndicatorHistoryFilterValue } from '@/types/macroIndicators'

export function renderIndicatorHistoryFilter(
  value: IndicatorHistoryFilterValue = 'all',
  onChange: (value: IndicatorHistoryFilterValue) => void = () => {},
) {
  return render(
    <IndicatorHistoryFilter value={value} onChange={onChange} />,
  )
}

export function getFilterButton(label: string) {
  return screen.getByRole('button', { name: label })
}

export function getFilterSelect() {
  return screen.getByRole('combobox', { name: 'Indicator filter' })
}

export async function selectIndicatorFilter(user: UserEvent, label: string) {
  await user.click(getFilterButton(label))
}

export async function selectIndicatorFilterOption(
  user: UserEvent,
  value: IndicatorHistoryFilterValue,
) {
  await user.selectOptions(getFilterSelect(), value)
}

export function expectFilterSelected(label: string) {
  expect(getFilterButton(label)).toHaveAttribute('aria-pressed', 'true')
}

export function expectFilterNotSelected(label: string) {
  expect(getFilterButton(label)).toHaveAttribute('aria-pressed', 'false')
}

export function expectFilterSelectValue(value: IndicatorHistoryFilterValue) {
  expect(getFilterSelect()).toHaveValue(value)
}
