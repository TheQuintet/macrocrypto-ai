import { useMutation, useQueryClient } from '@tanstack/react-query'
import {
  createExampleItem,
  exampleItemsQueryKey,
  type CreateExampleItemInput,
} from '@/api/example'

/** Example mutation pattern: sync/update remote data and refresh cache. */
export function useCreateExampleItemMutation() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (input: CreateExampleItemInput) => createExampleItem(input),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: exampleItemsQueryKey })
    },
  })
}
