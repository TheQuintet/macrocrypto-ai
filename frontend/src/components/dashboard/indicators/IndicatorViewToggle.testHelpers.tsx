import { render, screen } from '@testing-library/react'
import type { UserEvent } from '@testing-library/user-event'
import { expect } from 'vitest'
import { IndicatorViewToggle } from '@/components/dashboard/indicators/IndicatorViewToggle'
import type { MacroIndicatorView } from '@/types/macroIndicators'

export function renderViewToggle(
  value: MacroIndicatorView = 'current',
  onChange: (view: MacroIndicatorView) => void = () => {},
) {
  return render(<IndicatorViewToggle value={value} onChange={onChange} />)
}

export function getViewButton(label: string) {
  return screen.getByRole('button', { name: label })
}

export async function selectIndicatorView(user: UserEvent, label: string) {
  await user.click(getViewButton(label))
}

export function expectViewSelected(label: string) {
  expect(getViewButton(label)).toHaveAttribute('aria-pressed', 'true')
}

export function expectViewNotSelected(label: string) {
  expect(getViewButton(label)).toHaveAttribute('aria-pressed', 'false')
}
