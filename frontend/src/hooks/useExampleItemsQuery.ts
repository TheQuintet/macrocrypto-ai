import { useQuery } from '@tanstack/react-query'
import { exampleItemsQueryKey, fetchExampleItems } from '@/api/example'
import type { ExampleItem } from '@/types/example'

/** Example query pattern: fetch and cache remote data. */
export function useExampleItemsQuery() {
  return useQuery<ExampleItem[], Error>({
    queryKey: exampleItemsQueryKey,
    queryFn: fetchExampleItems,
  })
}
