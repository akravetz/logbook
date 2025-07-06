import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { QueryClient, QueryClientProvider, useQueryClient } from '@tanstack/react-query'
import { useRouter } from 'next/navigation'
import { useSession } from 'next-auth/react'

import { WorkoutsListScreen } from './workouts-list-screen'
import { AddSetModal } from '@/components/modals/add-set-modal'
import { EditSetModal } from '@/components/modals/edit-set-modal'
import { VoiceNoteModal } from '@/components/modals/voice-note-modal'
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
jest.mock('@/lib/stores/ui-store')
jest.mock('@/lib/cache-tags')
jest.mock('@/lib/hooks/use-optimistic-mutation')
jest.mock('@/lib/api/generated', () => ({
  useCreateWorkoutApiV1WorkoutsPost: jest.fn(),
  useCreateSetApiV1WorkoutsWorkoutIdExerciseExecutionsExerciseIdSetsPost: jest.fn(),
  useUpdateSetApiV1WorkoutsWorkoutIdExerciseExecutionsExerciseIdSetsSetIdPatch: jest.fn(),
  useUpdateExerciseExecutionApiV1WorkoutsWorkoutIdExerciseExecutionsExerciseIdPatch: jest.fn(),
  useGetExerciseExecutionApiV1WorkoutsWorkoutIdExerciseExecutionsExerciseIdGet: jest.fn(),
  useTranscribeAudioApiV1VoiceTranscribePost: jest.fn(),
  getListWorkoutsApiV1WorkoutsGetQueryOptions: jest.fn(),
}))
jest.mock('@tanstack/react-query', () => ({
  ...jest.requireActual('@tanstack/react-query'),
  useQueryClient: jest.fn(),
}))

// Import mocked functions
import { useTaggedListWorkouts } from '@/lib/hooks/use-tagged-queries'
import { useWorkoutStore } from '@/lib/stores/workout-store'
import { useUIStore } from '@/lib/stores/ui-store'
import { useCacheUtils } from '@/lib/cache-tags'
import {
  useCreateWorkoutApiV1WorkoutsPost,
  useCreateSetApiV1WorkoutsWorkoutIdExerciseExecutionsExerciseIdSetsPost,
  useUpdateSetApiV1WorkoutsWorkoutIdExerciseExecutionsExerciseIdSetsSetIdPatch,
  useUpdateExerciseExecutionApiV1WorkoutsWorkoutIdExerciseExecutionsExerciseIdPatch,
  useGetExerciseExecutionApiV1WorkoutsWorkoutIdExerciseExecutionsExerciseIdGet,
  useTranscribeAudioApiV1VoiceTranscribePost,
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

// Create test-specific QueryClient
const createTestQueryClient = () => new QueryClient({
  defaultOptions: {
    queries: { retry: false },
    mutations: { retry: false },
  },
})

describe('Workouts List Screen - Dependency Queueing Integration', () => {
  let mockWorkoutStore: any
  let mockUIStore: any
  let mockCacheUtils: any
  let mockCreateWorkoutMutation: any
  let mockCreateSetMutation: any
  let mockUpdateSetMutation: any
  let mockUpdateExerciseMutation: any
  let mockOptimisticMutations: { [key: string]: any }

  beforeEach(() => {
    jest.clearAllMocks()

    // Setup mock stores
    mockWorkoutStore = {
      activeWorkout: null,
      setActiveWorkout: jest.fn(),
      startTimer: jest.fn(),
      updateExerciseInWorkout: jest.fn(),
      addOptimisticSet: jest.fn(),
      reconcileSet: jest.fn(),
      cleanupFailedSetOperation: jest.fn(),
      addPendingOperation: jest.fn(),
    }

    mockUIStore = {
      modals: {
        addSet: { open: false, exerciseId: null },
        editSet: { open: false, exerciseId: null, setId: null, currentData: null },
        voiceNote: { open: false, exerciseId: null, exerciseName: null },
      },
      closeAllModals: jest.fn(),
    }

    mockCacheUtils = {
      invalidateWorkoutData: jest.fn(),
    }

    // Setup API mutations
    mockCreateWorkoutMutation = {
      mutateAsync: jest.fn(),
      isPending: false,
    }

    mockCreateSetMutation = {
      mutateAsync: jest.fn(),
      isPending: false,
    }

    mockUpdateSetMutation = {
      mutateAsync: jest.fn(),
      isPending: false,
    }

    mockUpdateExerciseMutation = {
      mutateAsync: jest.fn(),
      isPending: false,
    }

    // Track optimistic mutations per component
    mockOptimisticMutations = {}

    // Setup mocks
    ;(useRouter as jest.Mock).mockReturnValue(mockRouter)
    ;(useSession as jest.Mock).mockReturnValue(mockSession)
    ;(useWorkoutStore as jest.Mock).mockReturnValue(mockWorkoutStore)
    ;(useUIStore as jest.Mock).mockReturnValue(mockUIStore)
    ;(useCacheUtils as jest.Mock).mockReturnValue(mockCacheUtils)
    ;(useCreateWorkoutApiV1WorkoutsPost as jest.Mock).mockReturnValue(mockCreateWorkoutMutation)
    ;(useCreateSetApiV1WorkoutsWorkoutIdExerciseExecutionsExerciseIdSetsPost as jest.Mock).mockReturnValue(mockCreateSetMutation)
    ;(useUpdateSetApiV1WorkoutsWorkoutIdExerciseExecutionsExerciseIdSetsSetIdPatch as jest.Mock).mockReturnValue(mockUpdateSetMutation)
    ;(useUpdateExerciseExecutionApiV1WorkoutsWorkoutIdExerciseExecutionsExerciseIdPatch as jest.Mock).mockReturnValue(mockUpdateExerciseMutation)
    ;(useGetExerciseExecutionApiV1WorkoutsWorkoutIdExerciseExecutionsExerciseIdGet as jest.Mock).mockReturnValue({
      refetch: jest.fn(),
    })
    ;(useTranscribeAudioApiV1VoiceTranscribePost as jest.Mock).mockReturnValue({
      mutateAsync: jest.fn(),
    })
    ;(getListWorkoutsApiV1WorkoutsGetQueryOptions as jest.Mock).mockReturnValue({
      queryKey: ['workouts', { page: 1, size: 20 }],
      queryFn: jest.fn(),
    })

    ;(useTaggedListWorkouts as jest.Mock).mockReturnValue({
      data: createMockWorkoutList(),
      isLoading: false,
    })

    // Mock useOptimisticMutation to track different instances
    ;(useOptimisticMutation as jest.Mock).mockImplementation((config) => {
      const id = Math.random().toString(36).substring(7)
      const mock = {
        execute: jest.fn(),
        isExecuting: false,
        config, // Store config for inspection
      }
      mockOptimisticMutations[id] = mock
      return mock
    })
  })

  const renderWithProviders = (ui: React.ReactElement) => {
    const testQueryClient = createTestQueryClient()

    return render(
      <QueryClientProvider client={testQueryClient}>
        {ui}
      </QueryClientProvider>
    )
  }

  describe('Dependency Detection for Optimistic Workouts', () => {
    it('AddSetModal detects optimistic workout ID and configures dependency', () => {
      // Set up optimistic workout in store
      const optimisticWorkout = createOptimisticWorkout({ id: -123456789 })
      mockWorkoutStore.activeWorkout = optimisticWorkout

      mockUIStore.modals.addSet = {
        open: true,
        exerciseId: 1,
      }

      renderWithProviders(<AddSetModal />)

      // Find the AddSetModal's optimistic mutation configuration
      const addSetMutationConfigs = Object.values(mockOptimisticMutations).map(m => m.config)
      const addSetConfig = addSetMutationConfigs.find(config =>
        config.mutation === mockCreateSetMutation
      )

      expect(addSetConfig).toBeDefined()
      expect(addSetConfig.getDependency).toBeDefined()

      // Test dependency detection
      const dependency = addSetConfig.getDependency({
        workoutId: -123456789,
        exerciseId: 1,
        data: { weight: 135, clean_reps: 8, forced_reps: 0 }
      })

      expect(dependency).toBe('workout-creation-123456789')
      expect(addSetConfig.addPendingOperation).toBe(mockWorkoutStore.addPendingOperation)
    })

    it('EditSetModal detects optimistic workout ID and configures dependency', () => {
      const optimisticWorkout = createOptimisticWorkout({ id: -987654321 })
      mockWorkoutStore.activeWorkout = optimisticWorkout

      mockUIStore.modals.editSet = {
        open: true,
        exerciseId: 1,
        setId: 1,
        currentData: { weight: 135, clean_reps: 8, forced_reps: 0 }
      }

      renderWithProviders(<EditSetModal />)

      const editSetMutationConfigs = Object.values(mockOptimisticMutations).map(m => m.config)
      const editSetConfig = editSetMutationConfigs.find(config =>
        config.mutation === mockUpdateSetMutation
      )

      expect(editSetConfig).toBeDefined()
      expect(editSetConfig.getDependency).toBeDefined()

      const dependency = editSetConfig.getDependency({
        workoutId: -987654321,
        exerciseId: 1,
        setId: 1,
        data: { weight: 155 }
      })

      expect(dependency).toBe('workout-creation-987654321')
      expect(editSetConfig.addPendingOperation).toBe(mockWorkoutStore.addPendingOperation)
    })

    it('VoiceNoteModal detects optimistic workout ID and configures dependency', () => {
      const optimisticWorkout = createOptimisticWorkout({ id: -555444333 })
      mockWorkoutStore.activeWorkout = optimisticWorkout

      mockUIStore.modals.voiceNote = {
        open: true,
        exerciseId: 1,
        exerciseName: 'Bench Press'
      }

      renderWithProviders(<VoiceNoteModal />)

      const voiceNoteMutationConfigs = Object.values(mockOptimisticMutations).map(m => m.config)
      const voiceNoteConfig = voiceNoteMutationConfigs.find(config =>
        config.mutation === mockUpdateExerciseMutation
      )

      expect(voiceNoteConfig).toBeDefined()
      expect(voiceNoteConfig.getDependency).toBeDefined()

      const dependency = voiceNoteConfig.getDependency({
        workoutId: -555444333,
        exerciseId: 1,
        data: { note_text: 'Great set!' }
      })

      expect(dependency).toBe('workout-creation-555444333')
      expect(voiceNoteConfig.addPendingOperation).toBe(mockWorkoutStore.addPendingOperation)
    })
  })

  describe('No Dependency for Real Workouts', () => {
    it('modals return null dependency for positive workout IDs', () => {
      const realWorkout = createMockWorkout({ id: 42 })
      mockWorkoutStore.activeWorkout = realWorkout

      mockUIStore.modals.addSet = { open: true, exerciseId: 1 }
      mockUIStore.modals.editSet = { open: true, exerciseId: 1, setId: 1, currentData: {} }
      mockUIStore.modals.voiceNote = { open: true, exerciseId: 1, exerciseName: 'Test' }

      // Render all modals
      renderWithProviders(
        <div>
          <AddSetModal />
          <EditSetModal />
          <VoiceNoteModal />
        </div>
      )

      const allConfigs = Object.values(mockOptimisticMutations).map(m => m.config)

      // Test AddSet dependency
      const addSetConfig = allConfigs.find(config => config.mutation === mockCreateSetMutation)
      const addSetDependency = addSetConfig?.getDependency({
        workoutId: 42,
        exerciseId: 1,
        data: { weight: 135, clean_reps: 8, forced_reps: 0 }
      })
      expect(addSetDependency).toBeNull()

      // Test EditSet dependency
      const editSetConfig = allConfigs.find(config => config.mutation === mockUpdateSetMutation)
      const editSetDependency = editSetConfig?.getDependency({
        workoutId: 42,
        exerciseId: 1,
        setId: 1,
        data: { weight: 155 }
      })
      expect(editSetDependency).toBeNull()

      // Test VoiceNote dependency
      const voiceNoteConfig = allConfigs.find(config => config.mutation === mockUpdateExerciseMutation)
      const voiceNoteDependency = voiceNoteConfig?.getDependency({
        workoutId: 42,
        exerciseId: 1,
        data: { note_text: 'Great set!' }
      })
      expect(voiceNoteDependency).toBeNull()
    })
  })

  describe('End-to-End Optimistic Workflow', () => {
    it('creates optimistic workout and immediately allows dependent operations', async () => {
      const user = userEvent.setup()

      // Mock QueryClient for cache operations
      const mockQueryClient = {
        getQueryData: jest.fn().mockReturnValue(createMockWorkoutList()),
        setQueryData: jest.fn(),
      }
      ;(useQueryClient as jest.Mock).mockReturnValue(mockQueryClient)

      // Render WorkoutsList screen
      renderWithProviders(<WorkoutsListScreen />)

      // Click New Workout button
      const newWorkoutButton = screen.getByRole('button', { name: /new workout/i })
      await user.click(newWorkoutButton)

      // Verify optimistic mutation was called
      const workoutsMutations = Object.values(mockOptimisticMutations)
      const workoutCreationMutation = workoutsMutations.find(m =>
        m.config.mutation === mockCreateWorkoutMutation
      )

      expect(workoutCreationMutation?.execute).toHaveBeenCalledWith()

      // Simulate the optimistic addOptimistic function being called
      const addOptimistic = workoutCreationMutation?.config.addOptimistic
      const optimisticId = addOptimistic()

      // Verify optimistic setup
      expect(mockWorkoutStore.setActiveWorkout).toHaveBeenCalledWith(
        expect.objectContaining({
          id: expect.any(Number), // Negative number
        })
      )
      expect(mockWorkoutStore.startTimer).toHaveBeenCalled()
      expect(mockRouter.push).toHaveBeenCalledWith(expect.stringMatching(/\/workout\/-\d+/))

      // Now test that dependent operations can detect this optimistic workout
      const optimisticWorkout = mockWorkoutStore.setActiveWorkout.mock.calls[0][0]
      mockWorkoutStore.activeWorkout = optimisticWorkout

      // Setup AddSet modal to be open
      mockUIStore.modals.addSet = { open: true, exerciseId: 1 }

      // Render AddSet modal
      renderWithProviders(<AddSetModal />)

      // Find the AddSet mutation config
      const addSetMutations = Object.values(mockOptimisticMutations)
      const addSetConfig = addSetMutations.find(m => m.config.mutation === mockCreateSetMutation)?.config

      // Test that it detects the dependency
      const dependency = addSetConfig?.getDependency({
        workoutId: optimisticWorkout.id,
        exerciseId: 1,
        data: { weight: 135, clean_reps: 8, forced_reps: 0 }
      })

      expect(dependency).toBe(optimisticId)
    })
  })

  describe('Error Handling in Dependent Operations', () => {
    it('handles cleanup properly when optimistic workout creation fails', () => {
      const mockQueryClient = {
        getQueryData: jest.fn().mockReturnValue(createMockWorkoutList([
          createOptimisticWorkout({ id: -123456789 }),
          createMockWorkout({ id: 1 }),
        ])),
        setQueryData: jest.fn(),
      }
      ;(useQueryClient as jest.Mock).mockReturnValue(mockQueryClient)

      renderWithProviders(<WorkoutsListScreen />)

      const workoutsMutations = Object.values(mockOptimisticMutations)
      const workoutCreationMutation = workoutsMutations.find(m =>
        m.config.mutation === mockCreateWorkoutMutation
      )

      // Simulate cleanup after failed workout creation
      const cleanup = workoutCreationMutation?.config.cleanup
      cleanup('workout-creation-123456789')

      // Verify cleanup removes optimistic workout from cache
      expect(mockQueryClient.setQueryData).toHaveBeenCalledWith(
        expect.any(Array),
        expect.objectContaining({
          items: expect.arrayContaining([
            expect.objectContaining({ id: 1 }) // Only real workout remains
          ]),
          total: 1
        })
      )

      // Verify state cleanup
      expect(mockWorkoutStore.setActiveWorkout).toHaveBeenCalledWith(null)
      expect(mockRouter.push).toHaveBeenCalledWith('/workouts')
    })
  })

  describe('Consistent Dependency ID Format', () => {
    it('uses consistent workout-creation-{timestamp} format across all components', () => {
      const optimisticWorkout = createOptimisticWorkout({ id: -1234567890 })
      mockWorkoutStore.activeWorkout = optimisticWorkout

      // Setup all modals
      mockUIStore.modals = {
        addSet: { open: true, exerciseId: 1 },
        editSet: { open: true, exerciseId: 1, setId: 1, currentData: {} },
        voiceNote: { open: true, exerciseId: 1, exerciseName: 'Test' },
      }

      renderWithProviders(
        <div>
          <AddSetModal />
          <EditSetModal />
          <VoiceNoteModal />
        </div>
      )

      const allConfigs = Object.values(mockOptimisticMutations).map(m => m.config)

      // Test all dependency functions return same format
      allConfigs.forEach(config => {
        if (config.getDependency) {
          const dependency = config.getDependency({
            workoutId: -1234567890,
            exerciseId: 1,
            data: {}
          })
          expect(dependency).toBe('workout-creation-1234567890')
        }
      })
    })
  })
})
