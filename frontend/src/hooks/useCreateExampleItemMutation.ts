import { useMutation, useQueryClient } from '@tanstack/react-query'
import {
  createExampleItem,
  exampleItemsQueryKey,
  type CreateExampleItemInput,
  type ExampleItem,
} from '@/api/example'

/** Example mutation pattern: sync/update remote data and refresh cache. */
export function useCreateExampleItemMutation() {
  const queryClient = useQueryClient()

  return useMutation<ExampleItem, Error, CreateExampleItemInput>({
    mutationFn: (input) => createExampleItem(input),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: exampleItemsQueryKey })
    },
  })
}
