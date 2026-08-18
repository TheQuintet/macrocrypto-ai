import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { expect } from 'vitest'
import { ChartIntervalSwitcher } from '@/components/dashboard/controls/ChartIntervalSwitcher'
import type { ChartInterval } from '@/types/chart'

export function renderChartIntervalSwitcher(
  value: ChartInterval = '1h',
  onChange: (value: ChartInterval) => void = () => undefined,
) {
  return render(
    <ChartIntervalSwitcher value={value} onChange={onChange} />,
  )
}

export function getIntervalButton(label: string) {
  return screen.getByRole('button', { name: label })
}

export async function selectChartInterval(
  user: ReturnType<typeof userEvent.setup>,
  label: string,
) {
  await user.click(getIntervalButton(label))
}

export function expectIntervalSelected(label: string) {
  expect(getIntervalButton(label)).toHaveAttribute('aria-pressed', 'true')
}

export function expectTouchFriendlyIntervalButtons() {
  const group = screen.getByRole('group', { name: 'Chart interval' })
  expect(group).toHaveClass('w-full')
  expect(getIntervalButton('1h')).toHaveClass('min-h-11')
}
