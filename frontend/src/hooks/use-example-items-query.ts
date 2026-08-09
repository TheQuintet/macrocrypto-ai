import { useQuery } from '@tanstack/react-query'
import {
  exampleItemsQueryKey,
  fetchExampleItems,
  type ExampleItem,
} from '@/api/example'

/** Example query pattern: fetch and cache remote data. */
export function useExampleItemsQuery() {
  return useQuery<ExampleItem[], Error>({
    queryKey: exampleItemsQueryKey,
    queryFn: fetchExampleItems,
  })
}
