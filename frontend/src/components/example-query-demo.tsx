import { useState } from 'react'
import { toast } from 'sonner'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { useCreateExampleItemMutation } from '@/hooks/use-create-example-item-mutation'
import { useExampleItemsQuery } from '@/hooks/use-example-items-query'

/** Scaffold demo of TanStack Query query + mutation patterns. */
export function ExampleQueryDemo() {
  const [title, setTitle] = useState('')
  const { data, isPending, isError, error, isFetching } = useExampleItemsQuery()
  const createItem = useCreateExampleItemMutation()

  const handleCreate = () => {
    createItem.mutate(
      { title },
      {
        onSuccess: (item) => {
          setTitle('')
          toast.success('Item created', {
            description: item.title,
          })
        },
        onError: (mutationError) => {
          toast.error('Failed to create item', {
            description:
              mutationError instanceof Error
                ? mutationError.message
                : 'Unknown error',
          })
        },
      },
    )
  }

  return (
    <section className="flex w-full max-w-md flex-col gap-3 rounded-lg border p-4 text-left">
      <div className="space-y-1">
        <h2 className="text-sm font-medium">TanStack Query example</h2>
        <p className="text-xs text-muted-foreground">
          Server/API state via query + mutation (not Zustand).
        </p>
      </div>

      <div className="flex gap-2">
        <Input
          value={title}
          onChange={(event) => setTitle(event.target.value)}
          placeholder="New item title"
          aria-label="New example item title"
          disabled={createItem.isPending}
        />
        <Button
          type="button"
          size="sm"
          onClick={handleCreate}
          disabled={createItem.isPending || title.trim().length === 0}
        >
          {createItem.isPending ? 'Saving…' : 'Add'}
        </Button>
      </div>

      {isPending ? (
        <p className="text-sm text-muted-foreground">Loading items…</p>
      ) : null}

      {isError ? (
        <p className="text-sm text-destructive">
          {error instanceof Error ? error.message : 'Failed to load items'}
        </p>
      ) : null}

      {data ? (
        <ul className="space-y-2 text-sm">
          {data.map((item) => (
            <li
              key={item.id}
              className="flex items-center justify-between gap-2 rounded-md border px-3 py-2"
            >
              <span className="font-medium">{item.title}</span>
              <span className="shrink-0 text-xs text-muted-foreground">
                {isFetching ? 'Refreshing…' : 'Cached'}
              </span>
            </li>
          ))}
        </ul>
      ) : null}
    </section>
  )
}
