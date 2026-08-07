/**
 * Example remote-data helpers for TanStack Query patterns.
 * Replace with real API clients when the gateway is wired.
 */

export const exampleItemsQueryKey = ['example-items'] as const

export type ExampleItem = {
  id: string
  title: string
  updatedAt: string
}

const MOCK_LATENCY_MS = 350

let items: ExampleItem[] = [
  {
    id: '1',
    title: 'BTC market snapshot',
    updatedAt: new Date().toISOString(),
  },
  {
    id: '2',
    title: 'Macro indicator refresh',
    updatedAt: new Date().toISOString(),
  },
]

function delay(ms: number) {
  return new Promise((resolve) => setTimeout(resolve, ms))
}

/** Example GET — fetch/cache remote data via useQuery. */
export async function fetchExampleItems(): Promise<ExampleItem[]> {
  await delay(MOCK_LATENCY_MS)
  return items.map((item) => ({ ...item }))
}

export type CreateExampleItemInput = {
  title: string
}

/** Example POST — sync/update remote data via useMutation. */
export async function createExampleItem(
  input: CreateExampleItemInput,
): Promise<ExampleItem> {
  await delay(MOCK_LATENCY_MS)

  const title = input.title.trim()
  if (!title) {
    throw new Error('Title is required')
  }

  const created: ExampleItem = {
    id: String(Date.now()),
    title,
    updatedAt: new Date().toISOString(),
  }

  items = [created, ...items]
  return { ...created }
}
