import { useState } from 'react'
import type { UseMutationResult } from '@tanstack/react-query'
import { toast } from 'sonner'
import { logger } from '@/lib/logger'
import { isOptimisticId, generateOptimisticId, createPendingOperation, type PendingOperation } from '@/lib/utils/optimistic'

/**
 * Configuration for optimistic mutation hook
 */
export interface OptimisticMutationConfig<TData, TServerResponse> {
  /** Function to add optimistic data to local state */
  addOptimistic: (data: TData) => string

  /** Function to reconcile optimistic data with server response */
  reconcile: (optimisticId: string, serverData: TServerResponse) => void

  /** Function to cleanup failed optimistic data */
  cleanup: (optimisticId: string) => void

  /** TanStack Query mutation hook result */
  mutation: UseMutationResult<TServerResponse, Error, TData>

  /** Optional: Function to get dependency ID for queueing */
  getDependency?: (data: TData) => string | number | null

  /** Optional: Function to add pending operation to queue */
  addPendingOperation?: (operation: PendingOperation) => void

  /** Optional: Success message generator */
  onSuccess?: (data: TData, serverResponse?: TServerResponse) => string

  /** Optional: Error message generator */
  onError?: (error: Error, data: TData) => string
}

/**
 * Result of optimistic mutation hook
 */
export interface OptimisticMutationResult<TData> {
  /** Execute the optimistic mutation */
  execute: (data: TData) => Promise<void>

  /** Whether any operation is currently executing */
  isExecuting: boolean
}

/**
 * Hook for managing optimistic mutations with dependency queueing
 */
export function useOptimisticMutation<TData, TServerResponse>({
  addOptimistic,
  reconcile,
  cleanup,
  mutation,
  getDependency,
  addPendingOperation,
  onSuccess,
  onError
}: OptimisticMutationConfig<TData, TServerResponse>): OptimisticMutationResult<TData> {
  const [executingCount, setExecutingCount] = useState(0)

  const execute = async (data: TData): Promise<void> => {
    let optimisticId: string | null = null

    try {
      // Increment executing count
      setExecutingCount(prev => prev + 1)

      // 1. Add optimistic data immediately
      optimisticId = addOptimistic(data)

      // 2. Check for dependencies
      const dependency = getDependency?.(data)
      const hasDependency = dependency && isOptimisticId(dependency)

      if (hasDependency && addPendingOperation) {
        // 3a. Queue operation if dependency is optimistic
        const pendingOperation = createPendingOperation(
          'OPTIMISTIC_MUTATION',
          data,
          async () => {
            // Execute when dependency resolves
            try {
              const serverResponse = await mutation.mutateAsync(data)
              reconcile(optimisticId!, serverResponse)

              if (onSuccess) {
                toast.success(onSuccess(data, serverResponse))
              }
            } catch (error) {
              cleanup(optimisticId!)
              if (onError) {
                toast.error(onError(error as Error, data))
              }
              // Don't re-throw for queued operations - they should fail silently
              // with only cleanup and error toast
            }
          },
          () => {
            // Rollback on failure
            cleanup(optimisticId!)
          },
          dependency as string
        )

        addPendingOperation(pendingOperation)
      } else {
        // 3b. Execute immediately if no dependency or dependency is real
        try {
          const serverResponse = await mutation.mutateAsync(data)
          reconcile(optimisticId, serverResponse)

          if (onSuccess) {
            toast.success(onSuccess(data, serverResponse))
          }
        } catch (error) {
          cleanup(optimisticId)
          if (onError) {
            toast.error(onError(error as Error, data))
          }
          throw error
        }
      }
    } catch (error) {
      // Handle any errors in the optimistic update flow
      if (optimisticId) {
        cleanup(optimisticId)
      }

      logger.error('Optimistic mutation failed:', error)

      if (onError) {
        toast.error(onError(error as Error, data))
      }
    } finally {
      // Decrement executing count
      setExecutingCount(prev => prev - 1)
    }
  }

  return {
    execute,
    isExecuting: executingCount > 0
  }
}
