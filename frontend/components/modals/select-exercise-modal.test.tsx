import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { useSession } from 'next-auth/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { useWorkoutStore } from '@/lib/stores/workout-store'
import { useUIStore } from '@/lib/stores/ui-store'
import { useCacheUtils } from '@/lib/cache-tags'
import {
  useUpsertExerciseExecutionApiV1WorkoutsWorkoutIdExerciseExecutionsExerciseIdPut
} from '@/lib/api/generated'
import { useTaggedSearchExercises } from '@/lib/hooks/use-tagged-queries'
import { useExerciseDataCache } from '@/lib/search/exercise-data-cache'
import { SelectExerciseModal } from './select-exercise-modal'
import {
  createMockWorkout,
  createMockExercise,
  createMockExerciseSearchResults,
  createMockExerciseExecution
} from '@/lib/test-factories'
import type { MockMutation } from '@/lib/test-utils'

// Mock all dependencies
jest.mock('next-auth/react')
jest.mock('@/lib/stores/workout-store')
jest.mock('@/lib/stores/ui-store')
jest.mock('@/lib/cache-tags')
jest.mock('@/lib/api/generated')
jest.mock('@/lib/hooks/use-tagged-queries')
jest.mock('@/lib/search/exercise-data-cache')
jest.mock('sonner', () => ({
  toast: {
    error: jest.fn(),
    success: jest.fn(),
    info: jest.fn(),
  }
}))

// Create a test QueryClient
const createTestQueryClient = () => new QueryClient({
  defaultOptions: {
    queries: {
      retry: false, // Don't retry in tests
      staleTime: Infinity, // Prevent background refetches
    },
  },
})

// Custom render function with providers
const renderWithProviders = (ui: React.ReactElement) => {
  const queryClient = createTestQueryClient()
  return render(
    <QueryClientProvider client={queryClient}>
      {ui}
    </QueryClientProvider>
  )
}

const mockMutation: MockMutation = {
  mutateAsync: jest.fn(),
  mutate: jest.fn(),
  isPending: false,
  isError: false,
  error: null,
}

const mockWorkoutStore = {
  activeWorkout: createMockWorkout({ id: 1, exercise_executions: [] }),
  addOptimisticExercise: jest.fn().mockReturnValue('temp-12345'),
  reconcileExerciseExecution: jest.fn(),
  cleanupFailedOperations: jest.fn(),
}

const mockUIStore = {
  modals: { selectExercise: true },
  closeAllModals: jest.fn(),
  openAddNewExerciseModal: jest.fn(),
}

const mockCacheUtils = {
  invalidateWorkoutData: jest.fn(),
}

const mockSearchResults = createMockExerciseSearchResults([
  createMockExercise({ id: 1, name: 'Bench Press', body_part: 'chest' }),
  createMockExercise({ id: 2, name: 'Squat', body_part: 'legs' }),
])

describe('Exercise Selection User Workflow', () => {
  beforeEach(() => {
    jest.clearAllMocks()

    // Mock next-auth session
    ;(useSession as jest.Mock).mockReturnValue({
      data: {
        userId: '1',
        sessionToken: 'test-token',
        user: {
          name: 'Test User',
          email: 'test@example.com'
        }
      },
      status: 'authenticated'
    })

    // Mock exercise data cache
    ;(useExerciseDataCache as jest.Mock).mockReturnValue({
      data: [
        createMockExercise({ id: 1, name: 'Bench Press', body_part: 'chest' }),
        createMockExercise({ id: 2, name: 'Squat', body_part: 'legs' }),
      ],
      isLoading: false,
      error: null,
      refetch: jest.fn()
    })

    ;(useWorkoutStore as jest.Mock).mockReturnValue(mockWorkoutStore)
    ;(useUIStore as jest.Mock).mockReturnValue(mockUIStore)
    ;(useCacheUtils as jest.Mock).mockReturnValue(mockCacheUtils)
    ;(useUpsertExerciseExecutionApiV1WorkoutsWorkoutIdExerciseExecutionsExerciseIdPut as jest.Mock).mockReturnValue(mockMutation)
    ;(useTaggedSearchExercises as jest.Mock).mockReturnValue({
      data: mockSearchResults,
      isLoading: false,
    })
  })

  describe('Successful Exercise Addition', () => {
    it('shows exercise immediately when selected and closes modal', async () => {
      const user = userEvent.setup()

      renderWithProviders(<SelectExerciseModal />)

      // Find and click an exercise
      const benchPressButton = screen.getByRole('button', { name: /bench press/i })
      await user.click(benchPressButton)

      // Should immediately add optimistic exercise
      expect(mockWorkoutStore.addOptimisticExercise).toHaveBeenCalledWith({
        id: 1,
        name: 'Bench Press',
        body_part: 'chest',
        modality: 'BARBELL'
      })

      // Should close modal immediately (no waiting)
      expect(mockUIStore.closeAllModals).toHaveBeenCalled()

      // Should start background API call
      expect(mockMutation.mutate).toHaveBeenCalledWith({
        workoutId: 1,
        exerciseId: 1,
        data: {
          sets: [],
          exercise_order: 1,
        },
      }, expect.objectContaining({
        onSuccess: expect.any(Function),
        onError: expect.any(Function),
      }))
    })

    it('reconciles with server data when API succeeds', async () => {
      const user = userEvent.setup()

      renderWithProviders(<SelectExerciseModal />)

      const benchPressButton = screen.getByRole('button', { name: /bench press/i })
      await user.click(benchPressButton)

      // Simulate successful API response
      const onSuccessCallback = (mockMutation.mutate as jest.Mock).mock.calls[0][1].onSuccess
      const serverResponse = createMockExerciseExecution({
        exercise_id: 1,
        exercise_name: 'Bench Press',
      })

      await onSuccessCallback(serverResponse)

      // Should reconcile optimistic data with server response
      expect(mockWorkoutStore.reconcileExerciseExecution).toHaveBeenCalledWith(
        'temp-12345', // optimistic ID
        serverResponse
      )

      // Should invalidate cache for background sync
      expect(mockCacheUtils.invalidateWorkoutData).toHaveBeenCalled()
    })

    it('allows selecting multiple exercises rapidly', async () => {
      const user = userEvent.setup()

      renderWithProviders(<SelectExerciseModal />)

      // Rapidly select multiple exercises
      const benchPressButton = screen.getByRole('button', { name: /bench press/i })
      const squatButton = screen.getByRole('button', { name: /squat/i })

      await user.click(benchPressButton)
      await user.click(squatButton)

      // Both should be processed optimistically
      expect(mockWorkoutStore.addOptimisticExercise).toHaveBeenCalledTimes(2)
      expect(mockMutation.mutate).toHaveBeenCalledTimes(2)
    })
  })

  describe('Failed Exercise Addition', () => {
    it('removes exercise and shows error when API fails', async () => {
      const user = userEvent.setup()

      renderWithProviders(<SelectExerciseModal />)

      const benchPressButton = screen.getByRole('button', { name: /bench press/i })
      await user.click(benchPressButton)

      // Simulate API failure
      const onErrorCallback = (mockMutation.mutate as jest.Mock).mock.calls[0][1].onError
      const apiError = new Error('Network error')

      onErrorCallback(apiError)

      // Should clean up failed operation
      expect(mockWorkoutStore.cleanupFailedOperations).toHaveBeenCalledWith('temp-12345')
    })

    it('handles API errors gracefully without blocking UI', async () => {
      const user = userEvent.setup()

      // Mock API to always fail
      mockMutation.mutate.mockImplementation((_, { onError }) => {
        onError(new Error('API Error'))
      })

      renderWithProviders(<SelectExerciseModal />)

      const benchPressButton = screen.getByRole('button', { name: /bench press/i })
      await user.click(benchPressButton)

      // Modal should still close immediately despite API failure
      expect(mockUIStore.closeAllModals).toHaveBeenCalled()

      // Optimistic update should still happen
      expect(mockWorkoutStore.addOptimisticExercise).toHaveBeenCalled()

      // Cleanup should be called
      expect(mockWorkoutStore.cleanupFailedOperations).toHaveBeenCalled()
    })
  })

  describe('Exercise Search and Display', () => {
    it('groups exercises by body part', () => {
      renderWithProviders(<SelectExerciseModal />)

      // Should group exercises by body part
      expect(screen.getByText('Chest')).toBeInTheDocument()
      expect(screen.getByText('Legs')).toBeInTheDocument()

      // Exercises should appear under correct groups
      expect(screen.getByText('Bench Press')).toBeInTheDocument()
      expect(screen.getByText('Squat')).toBeInTheDocument()
    })

    it('shows loading state during search', () => {
      ;(useTaggedSearchExercises as jest.Mock).mockReturnValue({
        data: null,
        isLoading: true,
      })
      ;(useExerciseDataCache as jest.Mock).mockReturnValue({
        data: null,
        isLoading: true,
        error: null,
        refetch: jest.fn()
      })

      renderWithProviders(<SelectExerciseModal />)

      // Should not show specific exercises when loading
      expect(screen.queryByText('Bench Press')).not.toBeInTheDocument()
      expect(screen.queryByText('Squat')).not.toBeInTheDocument()

      // Should still show the modal title and search
      expect(screen.getByText('Select Exercise')).toBeInTheDocument()
      expect(screen.getByPlaceholderText('Search exercises...')).toBeInTheDocument()
    })

    it('handles empty search results', () => {
      ;(useTaggedSearchExercises as jest.Mock).mockReturnValue({
        data: { items: [], total: 0, page: 1, size: 50, pages: 0 },
        isLoading: false,
      })
      ;(useExerciseDataCache as jest.Mock).mockReturnValue({
        data: [],
        isLoading: false,
        error: null,
        refetch: jest.fn()
      })

      renderWithProviders(<SelectExerciseModal />)

      expect(screen.getByText('No exercises available')).toBeInTheDocument()
    })
  })

  describe('Modal Interactions', () => {
    it('closes modal when user cancels', async () => {
      const user = userEvent.setup()

      renderWithProviders(<SelectExerciseModal />)

      // Find and click close button or outside modal
      await user.keyboard('{Escape}')

      expect(mockUIStore.closeAllModals).toHaveBeenCalled()
    })

    it('opens add new exercise modal', async () => {
      const user = userEvent.setup()

      renderWithProviders(<SelectExerciseModal />)

      const addNewButton = screen.getByRole('button', { name: /add new exercise/i })
      await user.click(addNewButton)

      expect(mockUIStore.openAddNewExerciseModal).toHaveBeenCalled()
    })

    it('filters exercises based on search term', async () => {
      const user = userEvent.setup()

      // Mock filtered results for search
      ;(useExerciseDataCache as jest.Mock).mockReturnValue({
        data: [
          createMockExercise({ id: 1, name: 'Bench Press', body_part: 'chest' }),
        ],
        isLoading: false,
        error: null,
        refetch: jest.fn()
      })

      renderWithProviders(<SelectExerciseModal />)

      const searchInput = screen.getByPlaceholderText('Search exercises...')
      await user.type(searchInput, 'bench')

      // Wait for the search to filter results
      await waitFor(() => {
        expect(screen.getByText('Bench Press')).toBeInTheDocument()
        // Squat should not be shown when searching for "bench"
        expect(screen.queryByText('Squat')).not.toBeInTheDocument()
      })
    })
  })

  describe('No Active Workout Edge Case', () => {
    it('prevents exercise selection when no active workout', async () => {
      const user = userEvent.setup()

      // Mock no active workout
      ;(useWorkoutStore as jest.Mock).mockReturnValue({
        ...mockWorkoutStore,
        activeWorkout: null,
      })

      renderWithProviders(<SelectExerciseModal />)

      const benchPressButton = screen.getByRole('button', { name: /bench press/i })
      await user.click(benchPressButton)

      // Should not add exercise or make API call
      expect(mockWorkoutStore.addOptimisticExercise).not.toHaveBeenCalled()
      expect(mockMutation.mutate).not.toHaveBeenCalled()
    })
  })
})
