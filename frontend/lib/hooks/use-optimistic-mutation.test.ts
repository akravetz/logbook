import { renderHook, act, waitFor } from '@testing-library/react'
import { useOptimisticMutation } from './use-optimistic-mutation'
import type { UseMutationResult } from '@tanstack/react-query'

// Mock toast notifications
jest.mock('sonner', () => ({
  toast: {
    success: jest.fn(),
    error: jest.fn()
  }
}))

// Mock logger
jest.mock('@/lib/logger', () => ({
  logger: {
    error: jest.fn()
  }
}))

import { toast } from 'sonner'
import { logger } from '@/lib/logger'

// Test types and interfaces
interface TestData {
  id: number
  name: string
  value: number
}

interface OptimisticTestData extends TestData {
  id: string // Optimistic ID
  isOptimistic: true
}

interface ServerResponse {
  id: number
  name: string
  value: number
  created_at: string
}

// Mock mutation that we can control
const createMockMutation = (shouldSucceed = true, delay = 0): UseMutationResult<ServerResponse, any, TestData> => ({
  mutateAsync: jest.fn().mockImplementation((data: TestData) =>
    new Promise((resolve, reject) => {
      setTimeout(() => {
        if (shouldSucceed) {
          resolve({
            id: 123,
            name: data.name,
            value: data.value,
            created_at: new Date().toISOString()
          })
        } else {
          reject(new Error('API Error'))
        }
      }, delay)
    })
  ),
  mutate: jest.fn(),
  isPending: false,
  isError: false,
  isSuccess: false,
  isIdle: true,
  data: undefined,
  error: null,
  failureCount: 0,
  failureReason: null,
  isPaused: false,
  status: 'idle' as const,
  variables: undefined,
  submittedAt: 0,
  reset: jest.fn(),
})

describe('useOptimisticMutation', () => {
  // Mock functions for optimistic operations
  const mockAddOptimistic = jest.fn()
  const mockReconcile = jest.fn()
  const mockCleanup = jest.fn()
  const mockAddPendingOperation = jest.fn()
  const mockGetDependency = jest.fn()

  beforeEach(() => {
    jest.clearAllMocks()
    mockAddOptimistic.mockReturnValue('temp-123')
  })

  describe('Basic Optimistic Mutation Flow', () => {
    it('should execute optimistic update immediately', async () => {
      const mockMutation = createMockMutation(true)

      const { result } = renderHook(() => useOptimisticMutation({
        addOptimistic: mockAddOptimistic,
        reconcile: mockReconcile,
        cleanup: mockCleanup,
        mutation: mockMutation,
        onSuccess: () => 'Success message',
        onError: () => 'Error message'
      }))

      const testData = { id: 1, name: 'Test', value: 100 }

      await act(async () => {
        await result.current.execute(testData)
      })

      // Should call optimistic update immediately
      expect(mockAddOptimistic).toHaveBeenCalledWith(testData)
      expect(mockAddOptimistic).toHaveBeenCalledTimes(1)
    })

    it('should call API mutation with provided data', async () => {
      const mockMutation = createMockMutation(true)

      const { result } = renderHook(() => useOptimisticMutation({
        addOptimistic: mockAddOptimistic,
        reconcile: mockReconcile,
        cleanup: mockCleanup,
        mutation: mockMutation,
        onSuccess: () => 'Success message',
        onError: () => 'Error message'
      }))

      const testData = { id: 1, name: 'Test', value: 100 }

      await act(async () => {
        await result.current.execute(testData)
      })

      expect(mockMutation.mutateAsync).toHaveBeenCalledWith(testData)
    })

    it('should reconcile with server data on successful API call', async () => {
      const mockMutation = createMockMutation(true)

      const { result } = renderHook(() => useOptimisticMutation({
        addOptimistic: mockAddOptimistic,
        reconcile: mockReconcile,
        cleanup: mockCleanup,
        mutation: mockMutation,
        onSuccess: () => 'Success message',
        onError: () => 'Error message'
      }))

      const testData = { id: 1, name: 'Test', value: 100 }

      await act(async () => {
        await result.current.execute(testData)
      })

      await waitFor(() => {
        expect(mockReconcile).toHaveBeenCalledWith('temp-123', {
          id: 123,
          name: 'Test',
          value: 100,
          created_at: expect.any(String)
        })
      })
    })

    it('should show success toast on successful completion', async () => {
      const mockMutation = createMockMutation(true)

      const { result } = renderHook(() => useOptimisticMutation({
        addOptimistic: mockAddOptimistic,
        reconcile: mockReconcile,
        cleanup: mockCleanup,
        mutation: mockMutation,
        onSuccess: () => 'Operation successful',
        onError: () => 'Error message'
      }))

      await act(async () => {
        await result.current.execute({ id: 1, name: 'Test', value: 100 })
      })

      await waitFor(() => {
        expect(toast.success).toHaveBeenCalledWith('Operation successful')
      })
    })

    it('should cleanup and show error toast on API failure', async () => {
      const mockMutation = createMockMutation(false) // Will fail

      const { result } = renderHook(() => useOptimisticMutation({
        addOptimistic: mockAddOptimistic,
        reconcile: mockReconcile,
        cleanup: mockCleanup,
        mutation: mockMutation,
        onSuccess: () => 'Success message',
        onError: () => 'Operation failed'
      }))

      await act(async () => {
        await result.current.execute({ id: 1, name: 'Test', value: 100 })
      })

      await waitFor(() => {
        expect(mockCleanup).toHaveBeenCalledWith('temp-123')
        expect(toast.error).toHaveBeenCalledWith('Operation failed')
        expect(logger.error).toHaveBeenCalledWith('Optimistic mutation failed:', expect.any(Error))
      })
    })
  })

  describe('Dependency Queueing', () => {
    it('should execute immediately when no dependency is found', async () => {
      const mockMutation = createMockMutation(true)
      mockGetDependency.mockReturnValue(null) // No dependency

      const { result } = renderHook(() => useOptimisticMutation({
        addOptimistic: mockAddOptimistic,
        reconcile: mockReconcile,
        cleanup: mockCleanup,
        mutation: mockMutation,
        getDependency: mockGetDependency,
        addPendingOperation: mockAddPendingOperation,
        onSuccess: () => 'Success message',
        onError: () => 'Error message'
      }))

      await act(async () => {
        await result.current.execute({ id: 1, name: 'Test', value: 100 })
      })

      // Should execute immediately, not queue
      expect(mockMutation.mutateAsync).toHaveBeenCalled()
      expect(mockAddPendingOperation).not.toHaveBeenCalled()
    })

    it('should execute immediately when dependency is not optimistic', async () => {
      const mockMutation = createMockMutation(true)
      mockGetDependency.mockReturnValue(123) // Real dependency (number)

      const { result } = renderHook(() => useOptimisticMutation({
        addOptimistic: mockAddOptimistic,
        reconcile: mockReconcile,
        cleanup: mockCleanup,
        mutation: mockMutation,
        getDependency: mockGetDependency,
        addPendingOperation: mockAddPendingOperation,
        onSuccess: () => 'Success message',
        onError: () => 'Error message'
      }))

      await act(async () => {
        await result.current.execute({ id: 1, name: 'Test', value: 100 })
      })

      // Should execute immediately since dependency is real
      expect(mockMutation.mutateAsync).toHaveBeenCalled()
      expect(mockAddPendingOperation).not.toHaveBeenCalled()
    })

    it('should queue operation when dependency is optimistic', async () => {
      const mockMutation = createMockMutation(true)
      mockGetDependency.mockReturnValue('temp-parent-456') // Optimistic dependency

      const { result } = renderHook(() => useOptimisticMutation({
        addOptimistic: mockAddOptimistic,
        reconcile: mockReconcile,
        cleanup: mockCleanup,
        mutation: mockMutation,
        getDependency: mockGetDependency,
        addPendingOperation: mockAddPendingOperation,
        onSuccess: () => 'Success message',
        onError: () => 'Error message'
      }))

      await act(async () => {
        await result.current.execute({ id: 1, name: 'Test', value: 100 })
      })

      // Should queue operation, not execute immediately
      expect(mockMutation.mutateAsync).not.toHaveBeenCalled()
      expect(mockAddPendingOperation).toHaveBeenCalled()

      // Verify pending operation structure
      const pendingOp = mockAddPendingOperation.mock.calls[0][0]
      expect(pendingOp).toMatchObject({
        id: expect.stringMatching(/^temp-/),
        type: 'OPTIMISTIC_MUTATION',
        dependsOn: 'temp-parent-456',
        data: { id: 1, name: 'Test', value: 100 }
      })
      expect(typeof pendingOp.execute).toBe('function')
      expect(typeof pendingOp.rollback).toBe('function')
    })

    it('should execute queued operation when called manually', async () => {
      const mockMutation = createMockMutation(true)
      mockGetDependency.mockReturnValue('temp-parent-456')

      const { result } = renderHook(() => useOptimisticMutation({
        addOptimistic: mockAddOptimistic,
        reconcile: mockReconcile,
        cleanup: mockCleanup,
        mutation: mockMutation,
        getDependency: mockGetDependency,
        addPendingOperation: mockAddPendingOperation,
        onSuccess: () => 'Success message',
        onError: () => 'Error message'
      }))

      await act(async () => {
        await result.current.execute({ id: 1, name: 'Test', value: 100 })
      })

      // Get the queued operation and execute it
      const pendingOp = mockAddPendingOperation.mock.calls[0][0]

      await act(async () => {
        await pendingOp.execute()
      })

      // Now the API should be called
      expect(mockMutation.mutateAsync).toHaveBeenCalledWith({ id: 1, name: 'Test', value: 100 })
    })

    it('should rollback queued operation on failure', async () => {
      const mockMutation = createMockMutation(false) // Will fail
      mockGetDependency.mockReturnValue('temp-parent-456')

      const { result } = renderHook(() => useOptimisticMutation({
        addOptimistic: mockAddOptimistic,
        reconcile: mockReconcile,
        cleanup: mockCleanup,
        mutation: mockMutation,
        getDependency: mockGetDependency,
        addPendingOperation: mockAddPendingOperation,
        onSuccess: () => 'Success message',
        onError: () => 'Error message'
      }))

      await act(async () => {
        await result.current.execute({ id: 1, name: 'Test', value: 100 })
      })

      // Get the queued operation and execute it (will fail)
      const pendingOp = mockAddPendingOperation.mock.calls[0][0]

      await act(async () => {
        await pendingOp.execute()
      })

      // Should have called rollback (which calls cleanup)
      expect(mockCleanup).toHaveBeenCalledWith('temp-123')
    })
  })

  describe('Hook State Management', () => {
    it('should track isExecuting state during operation', async () => {
      const mockMutation = createMockMutation(true, 100) // 100ms delay

      const { result } = renderHook(() => useOptimisticMutation({
        addOptimistic: mockAddOptimistic,
        reconcile: mockReconcile,
        cleanup: mockCleanup,
        mutation: mockMutation,
        onSuccess: () => 'Success message',
        onError: () => 'Error message'
      }))

      expect(result.current.isExecuting).toBe(false)

      act(() => {
        result.current.execute({ id: 1, name: 'Test', value: 100 })
      })

      expect(result.current.isExecuting).toBe(true)

      await waitFor(() => {
        expect(result.current.isExecuting).toBe(false)
      })
    })

    it('should handle multiple concurrent executions', async () => {
      const mockMutation = createMockMutation(true, 50)

      const { result } = renderHook(() => useOptimisticMutation({
        addOptimistic: mockAddOptimistic,
        reconcile: mockReconcile,
        cleanup: mockCleanup,
        mutation: mockMutation,
        onSuccess: () => 'Success message',
        onError: () => 'Error message'
      }))

      // Execute multiple operations concurrently
      await act(async () => {
        await Promise.all([
          result.current.execute({ id: 1, name: 'Test1', value: 100 }),
          result.current.execute({ id: 2, name: 'Test2', value: 200 }),
          result.current.execute({ id: 3, name: 'Test3', value: 300 })
        ])
      })

      // All should have been processed
      expect(mockAddOptimistic).toHaveBeenCalledTimes(3)
      expect(mockMutation.mutateAsync).toHaveBeenCalledTimes(3)
      expect(mockReconcile).toHaveBeenCalledTimes(3)
    })
  })

  describe('Error Handling', () => {
    it('should handle errors in optimistic update', async () => {
      const mockMutation = createMockMutation(true)
      const faultyAddOptimistic = jest.fn().mockImplementation(() => {
        throw new Error('Optimistic update failed')
      })

      const { result } = renderHook(() => useOptimisticMutation({
        addOptimistic: faultyAddOptimistic,
        reconcile: mockReconcile,
        cleanup: mockCleanup,
        mutation: mockMutation,
        onSuccess: () => 'Success message',
        onError: () => 'Error message'
      }))

      await act(async () => {
        await result.current.execute({ id: 1, name: 'Test', value: 100 })
      })

      expect(logger.error).toHaveBeenCalledWith('Optimistic mutation failed:', expect.any(Error))
      expect(toast.error).toHaveBeenCalledWith('Error message')
    })

    it('should handle errors in reconciliation', async () => {
      const mockMutation = createMockMutation(true)
      const faultyReconcile = jest.fn().mockImplementation(() => {
        throw new Error('Reconciliation failed')
      })

      const { result } = renderHook(() => useOptimisticMutation({
        addOptimistic: mockAddOptimistic,
        reconcile: faultyReconcile,
        cleanup: mockCleanup,
        mutation: mockMutation,
        onSuccess: () => 'Success message',
        onError: () => 'Error message'
      }))

      await act(async () => {
        await result.current.execute({ id: 1, name: 'Test', value: 100 })
      })

      await waitFor(() => {
        expect(logger.error).toHaveBeenCalledWith('Optimistic mutation failed:', expect.any(Error))
        expect(mockCleanup).toHaveBeenCalledWith('temp-123')
      })
    })
  })

  describe('Dynamic Message Generation', () => {
    it('should support dynamic success messages', async () => {
      const mockMutation = createMockMutation(true)

      const { result } = renderHook(() => useOptimisticMutation({
        addOptimistic: mockAddOptimistic,
        reconcile: mockReconcile,
        cleanup: mockCleanup,
        mutation: mockMutation,
        onSuccess: (data) => `Successfully created ${data.name}`,
        onError: () => 'Error message'
      }))

      await act(async () => {
        await result.current.execute({ id: 1, name: 'TestItem', value: 100 })
      })

      await waitFor(() => {
        expect(toast.success).toHaveBeenCalledWith('Successfully created TestItem')
      })
    })

    it('should support dynamic error messages', async () => {
      const mockMutation = createMockMutation(false)

      const { result } = renderHook(() => useOptimisticMutation({
        addOptimistic: mockAddOptimistic,
        reconcile: mockReconcile,
        cleanup: mockCleanup,
        mutation: mockMutation,
        onSuccess: () => 'Success message',
        onError: (error, data) => `Failed to create ${data.name}: ${error.message}`
      }))

      await act(async () => {
        await result.current.execute({ id: 1, name: 'TestItem', value: 100 })
      })

      await waitFor(() => {
        expect(toast.error).toHaveBeenCalledWith('Failed to create TestItem: API Error')
      })
    })
  })

  describe('Optional Features', () => {
    it('should work without dependency handling', async () => {
      const mockMutation = createMockMutation(true)

      const { result } = renderHook(() => useOptimisticMutation({
        addOptimistic: mockAddOptimistic,
        reconcile: mockReconcile,
        cleanup: mockCleanup,
        mutation: mockMutation,
        onSuccess: () => 'Success message',
        onError: () => 'Error message'
        // No getDependency or addPendingOperation
      }))

      await act(async () => {
        await result.current.execute({ id: 1, name: 'Test', value: 100 })
      })

      // Should work normally without dependency features
      expect(mockAddOptimistic).toHaveBeenCalled()
      expect(mockMutation.mutateAsync).toHaveBeenCalled()
      expect(mockReconcile).toHaveBeenCalled()
    })

    it('should work without toast messages', async () => {
      const mockMutation = createMockMutation(true)

      const { result } = renderHook(() => useOptimisticMutation({
        addOptimistic: mockAddOptimistic,
        reconcile: mockReconcile,
        cleanup: mockCleanup,
        mutation: mockMutation
        // No onSuccess or onError
      }))

      await act(async () => {
        await result.current.execute({ id: 1, name: 'Test', value: 100 })
      })

      // Should work without showing toasts
      expect(mockAddOptimistic).toHaveBeenCalled()
      expect(mockMutation.mutateAsync).toHaveBeenCalled()
      expect(mockReconcile).toHaveBeenCalled()
      expect(toast.success).not.toHaveBeenCalled()
    })
  })
})
