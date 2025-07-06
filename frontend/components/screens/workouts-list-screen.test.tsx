import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { QueryClient, QueryClientProvider, useQueryClient } from '@tanstack/react-query'
import { useRouter } from 'next/navigation'
import { useSession } from 'next-auth/react'
import { toast } from 'sonner'

import { WorkoutsListScreen } from './workouts-list-screen'
import {
  createMockWorkout,
  createMockWorkoutList,
  createOptimisticWorkout
} from '@/lib/test-factories'

// Mock external dependencies
jest.mock('next/navigation')
jest.mock('next-auth/react')
jest.mock('sonner')
jest.mock('@/lib/hooks/use-tagged-queries')
jest.mock('@/lib/stores/workout-store')
jest.mock('@/lib/cache-tags')
jest.mock('@/lib/api/generated')
jest.mock('@/lib/hooks/use-optimistic-mutation')
jest.mock('@tanstack/react-query', () => ({
  ...jest.requireActual('@tanstack/react-query'),
  useQueryClient: jest.fn(),
}))

// Import mocked functions
import { useTaggedListWorkouts } from '@/lib/hooks/use-tagged-queries'
import { useWorkoutStore } from '@/lib/stores/workout-store'
import { useCacheUtils } from '@/lib/cache-tags'
import {
  useCreateWorkoutApiV1WorkoutsPost,
  getListWorkoutsApiV1WorkoutsGetQueryOptions
} from '@/lib/api/generated'
import { useOptimisticMutation } from '@/lib/hooks/use-optimistic-mutation'

const mockRouter = {
  push: jest.fn(),
  replace: jest.fn(),
  back: jest.fn(),
  forward: jest.fn(),
  refresh: jest.fn(),
  prefetch: jest.fn(),
}

const mockSession = {
  data: {
    userId: '1',
    sessionToken: 'test-token',
    user: {
      name: 'John Doe',
      email: 'john@example.com'
    }
  },
  status: 'authenticated'
}

const mockWorkoutStore = {
  setActiveWorkout: jest.fn(),
  startTimer: jest.fn(),
  addPendingOperation: jest.fn(),
}

const mockCacheUtils = {
  invalidateWorkoutData: jest.fn(),
}

const mockCreateWorkoutMutation = {
  mutateAsync: jest.fn(),
  isPending: false,
}

const mockOptimisticMutation = {
  execute: jest.fn(),
  isExecuting: false,
}

const mockQueryOptions = {
  queryKey: ['workouts', { page: 1, size: 20 }],
  queryFn: jest.fn(),
}

// Create test-specific QueryClient
const createTestQueryClient = () => new QueryClient({
  defaultOptions: {
    queries: { retry: false },
    mutations: { retry: false },
  },
})

// Custom render function with providers
const renderWithProviders = (ui: React.ReactElement) => {
  const testQueryClient = createTestQueryClient()

  return render(
    <QueryClientProvider client={testQueryClient}>
      {ui}
    </QueryClientProvider>
  )
}

describe('WorkoutsListScreen', () => {
  beforeEach(() => {
    jest.clearAllMocks()

    // Setup default mocks
    ;(useRouter as jest.Mock).mockReturnValue(mockRouter)
    ;(useSession as jest.Mock).mockReturnValue(mockSession)
    ;(useWorkoutStore as jest.Mock).mockReturnValue(mockWorkoutStore)
    ;(useCacheUtils as jest.Mock).mockReturnValue(mockCacheUtils)
    ;(useCreateWorkoutApiV1WorkoutsPost as jest.Mock).mockReturnValue(mockCreateWorkoutMutation)
    ;(useOptimisticMutation as jest.Mock).mockReturnValue(mockOptimisticMutation)
    ;(getListWorkoutsApiV1WorkoutsGetQueryOptions as jest.Mock).mockReturnValue(mockQueryOptions)
    ;(useTaggedListWorkouts as jest.Mock).mockReturnValue({
      data: createMockWorkoutList(),
      isLoading: false,
    })
  })

  describe('Rendering and Basic Functionality', () => {
    it('displays user greeting with first name', () => {
      renderWithProviders(<WorkoutsListScreen />)

      expect(screen.getByText('John')).toBeInTheDocument()
    })

    it('displays workout list when data is loaded', () => {
      const mockWorkouts = [
        createMockWorkout({ id: 1 }),
        createMockWorkout({ id: 2 }),
      ]

      ;(useTaggedListWorkouts as jest.Mock).mockReturnValue({
        data: createMockWorkoutList(mockWorkouts),
        isLoading: false,
      })

      renderWithProviders(<WorkoutsListScreen />)

      expect(screen.getByText('Workouts')).toBeInTheDocument()
      expect(screen.getByRole('button', { name: /new workout/i })).toBeInTheDocument()
    })

    it('shows loading skeleton when data is loading', () => {
      ;(useTaggedListWorkouts as jest.Mock).mockReturnValue({
        data: null,
        isLoading: true,
      })

      renderWithProviders(<WorkoutsListScreen />)

      // Should show loading skeletons
      const skeletons = screen.getAllByRole('generic')
      expect(skeletons.length).toBeGreaterThan(0)
    })

    it('shows empty state when no workouts exist', () => {
      ;(useTaggedListWorkouts as jest.Mock).mockReturnValue({
        data: { items: [], total: 0, page: 1, size: 20, pages: 0 },
        isLoading: false,
      })

      renderWithProviders(<WorkoutsListScreen />)

      expect(screen.getByText('No workouts yet')).toBeInTheDocument()
      expect(screen.getByText(/tap.*new workout.*to get started/i)).toBeInTheDocument()
    })
  })

  describe('Optimistic Workout Creation User Flow', () => {
    it('creates workout optimistically and navigates immediately when user clicks New Workout', async () => {
      const user = userEvent.setup()
      renderWithProviders(<WorkoutsListScreen />)

      const newWorkoutButton = screen.getByRole('button', { name: /new workout/i })
      await user.click(newWorkoutButton)

      // Should execute optimistic mutation
      expect(mockOptimisticMutation.execute).toHaveBeenCalledWith()
      expect(mockOptimisticMutation.execute).toHaveBeenCalledTimes(1)
    })

    it('shows creating state while optimistic mutation is executing', () => {
      ;(useOptimisticMutation as jest.Mock).mockReturnValue({
        ...mockOptimisticMutation,
        isExecuting: true,
      })

      renderWithProviders(<WorkoutsListScreen />)

      const newWorkoutButton = screen.getByRole('button', { name: /creating.../i })
      expect(newWorkoutButton).toBeInTheDocument()
      expect(newWorkoutButton).toBeDisabled()
    })
  })

  describe('Optimistic Mutation Configuration', () => {
    it('configures optimistic mutation with correct addOptimistic function', () => {
      renderWithProviders(<WorkoutsListScreen />)

      expect(useOptimisticMutation).toHaveBeenCalledWith(
        expect.objectContaining({
          addOptimistic: expect.any(Function),
          reconcile: expect.any(Function),
          cleanup: expect.any(Function),
          mutation: mockCreateWorkoutMutation,
          onSuccess: expect.any(Function),
          onError: expect.any(Function),
        })
      )
    })

    it('creates optimistic workout with negative ID and correct structure', () => {
      // Mock QueryClient methods
      const mockQueryClient = {
        getQueryData: jest.fn().mockReturnValue(createMockWorkoutList()),
        setQueryData: jest.fn(),
      }

      // Mock the QueryClient hook
      ;(useQueryClient as jest.Mock).mockReturnValue(mockQueryClient)

      renderWithProviders(<WorkoutsListScreen />)

      const mockCall = (useOptimisticMutation as jest.Mock).mock.calls[0][0]
      const addOptimistic = mockCall.addOptimistic

      const optimisticId = addOptimistic()

      // Should create workout with negative ID
      expect(optimisticId).toMatch(/workout-creation-\d+/)

      // Should set active workout and start timer
      expect(mockWorkoutStore.setActiveWorkout).toHaveBeenCalled()
      expect(mockWorkoutStore.startTimer).toHaveBeenCalled()

      // Should navigate to workout page
      expect(mockRouter.push).toHaveBeenCalledWith(expect.stringMatching(/\/workout\/-\d+/))
    })
  })

  describe('Cache Management During Optimistic Updates', () => {
    let mockQueryClient: any

    beforeEach(() => {
      mockQueryClient = {
        getQueryData: jest.fn(),
        setQueryData: jest.fn(),
      }
      ;(useQueryClient as jest.Mock).mockReturnValue(mockQueryClient)
    })

    it('updates workout list cache immediately when adding optimistic workout', () => {
      const initialWorkouts = [createMockWorkout({ id: 1 })]
      mockQueryClient.getQueryData.mockReturnValue(createMockWorkoutList(initialWorkouts))

      renderWithProviders(<WorkoutsListScreen />)

      const mockCall = (useOptimisticMutation as jest.Mock).mock.calls[0][0]
      const addOptimistic = mockCall.addOptimistic

      addOptimistic()

      // Should update cache with optimistic workout at beginning of list
      expect(mockQueryClient.setQueryData).toHaveBeenCalledWith(
        expect.any(Array),
        expect.objectContaining({
          items: expect.arrayContaining([
            expect.objectContaining({ id: expect.any(Number) }), // Optimistic workout (negative ID)
            ...initialWorkouts
          ]),
          total: initialWorkouts.length + 1
        })
      )
    })

    it('removes optimistic workout from cache on error cleanup', () => {
      const workoutsWithOptimistic = [
        createOptimisticWorkout({ id: -123456789 }),
        createMockWorkout({ id: 1 }),
        createMockWorkout({ id: 2 }),
      ]

      mockQueryClient.getQueryData.mockReturnValue(createMockWorkoutList(workoutsWithOptimistic))

      renderWithProviders(<WorkoutsListScreen />)

      const mockCall = (useOptimisticMutation as jest.Mock).mock.calls[0][0]
      const cleanup = mockCall.cleanup

      cleanup('workout-creation-123456789')

      // Should remove optimistic workouts (negative IDs) and adjust total count
      expect(mockQueryClient.setQueryData).toHaveBeenCalledWith(
        expect.any(Array),
        expect.objectContaining({
          items: expect.arrayContaining([
            expect.objectContaining({ id: 1 }),
            expect.objectContaining({ id: 2 }),
          ]),
          total: 2 // Reduced by 1
        })
      )

      // Should clear active workout and navigate back
      expect(mockWorkoutStore.setActiveWorkout).toHaveBeenCalledWith(null)
      expect(mockRouter.push).toHaveBeenCalledWith('/workouts')
    })
  })

  describe('Server Reconciliation', () => {
    it('reconciles optimistic workout with server response', async () => {
      const serverWorkout = createMockWorkout({ id: 42 })

      renderWithProviders(<WorkoutsListScreen />)

      const mockCall = (useOptimisticMutation as jest.Mock).mock.calls[0][0]
      const reconcile = mockCall.reconcile

      await reconcile('workout-creation-123456789', serverWorkout)

      // Should update active workout with server data
      expect(mockWorkoutStore.setActiveWorkout).toHaveBeenCalledWith(serverWorkout)

      // Should invalidate workout data cache
      expect(mockCacheUtils.invalidateWorkoutData).toHaveBeenCalled()

      // Should navigate to real workout ID
      expect(mockRouter.replace).toHaveBeenCalledWith('/workout/42')
    })
  })

  describe('Success and Error Toast Messages', () => {
    it('configures success message for optimistic mutation', () => {
      renderWithProviders(<WorkoutsListScreen />)

      const mockCall = (useOptimisticMutation as jest.Mock).mock.calls[0][0]
      const onSuccess = mockCall.onSuccess

      expect(onSuccess()).toBe('New workout created successfully')
    })

    it('configures error message for optimistic mutation', () => {
      renderWithProviders(<WorkoutsListScreen />)

      const mockCall = (useOptimisticMutation as jest.Mock).mock.calls[0][0]
      const onError = mockCall.onError

      expect(onError()).toBe('Failed to create workout')
    })
  })

  describe('User Authentication Integration', () => {
    it('handles missing user name gracefully', () => {
      ;(useSession as jest.Mock).mockReturnValue({
        data: {
          userId: '1',
          sessionToken: 'test-token',
          user: {
            name: null,
            email: 'john@example.com'
          }
        },
        status: 'authenticated'
      })

      renderWithProviders(<WorkoutsListScreen />)

      expect(screen.getByText('there')).toBeInTheDocument()
    })

    it('displays user avatar initial when name is available', () => {
      renderWithProviders(<WorkoutsListScreen />)

      expect(screen.getByText('J')).toBeInTheDocument() // First letter of "John"
    })

    it('displays default avatar when user name is missing', () => {
      ;(useSession as jest.Mock).mockReturnValue({
        data: {
          userId: '1',
          sessionToken: 'test-token',
          user: {
            name: null,
            email: 'john@example.com'
          }
        },
        status: 'authenticated'
      })

      renderWithProviders(<WorkoutsListScreen />)

      expect(screen.getByText('U')).toBeInTheDocument() // Default initial
    })
  })

  describe('Workout Navigation', () => {
    it('navigates to existing workout when workout card is clicked', async () => {
      const user = userEvent.setup()
      const mockWorkouts = [createMockWorkout({ id: 5 })]

      ;(useTaggedListWorkouts as jest.Mock).mockReturnValue({
        data: createMockWorkoutList(mockWorkouts),
        isLoading: false,
      })

      renderWithProviders(<WorkoutsListScreen />)

      // Look for workout cards more specifically
      const workoutButtons = screen.getAllByRole('button')
      const workoutCard = workoutButtons.find(button =>
        button.textContent?.includes('Workout') && !button.textContent?.includes('New Workout')
      )

      expect(workoutCard).toBeDefined()
      await user.click(workoutCard!)

      expect(mockRouter.push).toHaveBeenCalledWith('/workout/5')
    })
  })

  describe('Accessibility', () => {
    it('has accessible button labels', () => {
      renderWithProviders(<WorkoutsListScreen />)

      expect(screen.getByRole('button', { name: /new workout/i })).toBeInTheDocument()
    })

    it('maintains button accessibility during loading state', () => {
      ;(useOptimisticMutation as jest.Mock).mockReturnValue({
        ...mockOptimisticMutation,
        isExecuting: true,
      })

      renderWithProviders(<WorkoutsListScreen />)

      const button = screen.getByRole('button', { name: /creating.../i })
      expect(button).toBeDisabled()
      expect(button).toHaveAttribute('disabled')
    })
  })
})
