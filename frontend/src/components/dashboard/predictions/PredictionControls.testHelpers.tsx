import { render, screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { expect } from 'vitest'
import { ConfidenceLevelSelector } from '@/components/dashboard/predictions/ConfidenceLevelSelector'
import { PredictionHorizonToggle } from '@/components/dashboard/predictions/PredictionHorizonToggle'

export const HORIZON_GROUP = 'Forecast horizon'
export const CONFIDENCE_GROUP = 'Confidence level'

export function renderPredictionControls() {
  return render(
    <>
      <PredictionHorizonToggle />
      <ConfidenceLevelSelector />
    </>,
  )
}

function getOption(groupName: string, label: string) {
  return within(screen.getByRole('group', { name: groupName })).getByRole(
    'button',
    { name: new RegExp(`^${label}$`) },
  )
}

export async function selectHorizon(label: string) {
  await userEvent.click(getOption(HORIZON_GROUP, label))
}

export async function selectConfidence(label: string) {
  await userEvent.click(getOption(CONFIDENCE_GROUP, label))
}

export function expectHorizonSelected(label: string) {
  expect(getOption(HORIZON_GROUP, label)).toHaveAttribute(
    'aria-pressed',
    'true',
  )
}

export function expectConfidenceSelected(label: string) {
  expect(getOption(CONFIDENCE_GROUP, label)).toHaveAttribute(
    'aria-pressed',
    'true',
  )
}

export function expectOptionsOffered(groupName: string, labels: string[]) {
  const options = within(screen.getByRole('group', { name: groupName }))
    .getAllByRole('button')
    .map((button) => button.textContent)

  expect(options).toEqual(labels)
}
