import { useQuery } from '@tanstack/react-query'
import { exampleItemsQueryKey, fetchExampleItems } from '@/api/example'

/** Example query pattern: fetch and cache remote data. */
export function useExampleItemsQuery() {
  return useQuery({
    queryKey: exampleItemsQueryKey,
    queryFn: fetchExampleItems,
  })
}
