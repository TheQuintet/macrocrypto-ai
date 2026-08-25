import { render, screen } from '@testing-library/react'
import type { UserEvent } from '@testing-library/user-event'
import { expect } from 'vitest'
import { IndicatorPeriodPicker } from '@/components/dashboard/indicators/IndicatorPeriodPicker'
import type { MacroIndicatorPeriod } from '@/types/macroIndicators'

export function renderPeriodPicker(
  value: MacroIndicatorPeriod = '90d',
  onChange: (period: MacroIndicatorPeriod) => void = () => {},
) {
  return render(<IndicatorPeriodPicker value={value} onChange={onChange} />)
}

export function getPeriodButton(label: string) {
  return screen.getByRole('button', { name: label })
}

export async function selectIndicatorPeriod(user: UserEvent, label: string) {
  await user.click(getPeriodButton(label))
}

export function expectPeriodSelected(label: string) {
  expect(getPeriodButton(label)).toHaveAttribute('aria-pressed', 'true')
}

export function expectPeriodNotSelected(label: string) {
  expect(getPeriodButton(label)).toHaveAttribute('aria-pressed', 'false')
}
