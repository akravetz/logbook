import { render, RenderOptions } from '@testing-library/react'
import { ReactElement } from 'react'
import { useSession } from 'next-auth/react'
import { useWorkoutStore } from '@/lib/stores/workout-store'
import { useUIStore } from '@/lib/stores/ui-store'
import { useCacheUtils } from '@/lib/cache-tags'
import {
  useFinishWorkoutApiV1WorkoutsWorkoutIdFinishPatch,
  useUpsertExerciseExecutionApiV1WorkoutsWorkoutIdExerciseExecutionsExerciseIdPut,
  useReorderExercisesApiV1WorkoutsWorkoutIdExerciseExecutionsReorderPatch
} from '@/lib/api/generated'
import { createMockWorkout } from './test-factories'
import type { WorkoutResponse } from '@/lib/api/model'

// Mock hook return types
export interface MockMutation {
  mutateAsync: jest.Mock
  isPending: boolean
  isError: boolean
  error: Error | null
}

export interface MockWorkoutStore {
  activeWorkout: WorkoutResponse | null
  workoutTimer: number
  timerInterval: NodeJS.Timeout | null
  stopTimer: jest.Mock
  resetTimer: jest.Mock
  setActiveWorkout: jest.Mock
  updateExerciseInWorkout: jest.Mock
  reorderExercises: jest.Mock
  startTimer: jest.Mock
  updateWorkoutTimer: jest.Mock
  addExerciseToWorkout: jest.Mock
  removeExerciseFromWorkout: jest.Mock
}

export interface MockUIStore {
  openSelectExerciseModal: jest.Mock
  openAddSetModal: jest.Mock
  openEditSetModal: jest.Mock
  openVoiceNoteModal: jest.Mock
  closeAllModals: jest.Mock
  modals: {
    selectExercise: boolean
    addNewExercise: boolean
    addSet: { open: boolean; exerciseId: number | null }
    editSet: { open: boolean; exerciseId: number | null; setId: number | null; currentData?: any }
    voiceNote: { open: boolean; exerciseId: number | null; exerciseName: string | null }
  }
  selectedExerciseForSet: any
  setSelectedExerciseForSet: jest.Mock
  openAddNewExerciseModal: jest.Mock
}

export interface MockSession {
  user?: {
    name?: string
    email?: string
    image?: string
  }
}

export interface MockCacheUtils {
  invalidateWorkoutData: jest.Mock
  invalidateExerciseData: jest.Mock
  invalidateUserData: jest.Mock
  invalidateAll: jest.Mock
}

export interface TestSetupOptions {
  workoutState?: Partial<MockWorkoutStore>
  uiState?: Partial<MockUIStore>
  sessionState?: MockSession
  cacheUtils?: Partial<MockCacheUtils>
  apiMocks?: {
    finishWorkout?: Partial<MockMutation>
    upsertExecution?: Partial<MockMutation>
    reorderExercises?: Partial<MockMutation>
  }
}

export const createMockMutation = (overrides: Partial<MockMutation> = {}): MockMutation => ({
  mutateAsync: jest.fn(),
  isPending: false,
  isError: false,
  error: null,
  ...overrides,
})

export const setupActiveWorkoutTest = (options: TestSetupOptions = {}) => {
  const mockWorkoutStore: MockWorkoutStore = {
    activeWorkout: createMockWorkout(),
    workoutTimer: 0,
    timerInterval: null,
    stopTimer: jest.fn(),
    resetTimer: jest.fn(),
    setActiveWorkout: jest.fn(),
    updateExerciseInWorkout: jest.fn(),
    reorderExercises: jest.fn(),
    startTimer: jest.fn(),
    updateWorkoutTimer: jest.fn(),
    addExerciseToWorkout: jest.fn(),
    removeExerciseFromWorkout: jest.fn(),
    ...options.workoutState,
  }

  const mockUIStore: MockUIStore = {
    openSelectExerciseModal: jest.fn(),
    openAddSetModal: jest.fn(),
    openEditSetModal: jest.fn(),
    openVoiceNoteModal: jest.fn(),
    closeAllModals: jest.fn(),
    openAddNewExerciseModal: jest.fn(),
    setSelectedExerciseForSet: jest.fn(),
    modals: {
      selectExercise: false,
      addNewExercise: false,
      addSet: { open: false, exerciseId: null },
      editSet: { open: false, exerciseId: null, setId: null },
      voiceNote: { open: false, exerciseId: null, exerciseName: null },
    },
    selectedExerciseForSet: null,
    ...options.uiState,
  }

  const mockSession: MockSession = {
    user: { name: 'Test User', email: 'test@example.com' },
    ...options.sessionState,
  }

  const mockCacheUtils: MockCacheUtils = {
    invalidateWorkoutData: jest.fn(),
    invalidateExerciseData: jest.fn(),
    invalidateUserData: jest.fn(),
    invalidateAll: jest.fn(),
    ...options.cacheUtils,
  }

  const mockFinishWorkout = createMockMutation(options.apiMocks?.finishWorkout)
  const mockUpsertExecution = createMockMutation(options.apiMocks?.upsertExecution)
  const mockReorderExercises = createMockMutation(options.apiMocks?.reorderExercises)

  // Setup all mocks
  ;(useWorkoutStore as jest.Mock).mockReturnValue(mockWorkoutStore)
  ;(useUIStore as jest.Mock).mockReturnValue(mockUIStore)
  ;(useSession as jest.Mock).mockReturnValue({ data: mockSession })
  ;(useCacheUtils as jest.Mock).mockReturnValue(mockCacheUtils)
  ;(useFinishWorkoutApiV1WorkoutsWorkoutIdFinishPatch as jest.Mock).mockReturnValue(mockFinishWorkout)
  ;(useUpsertExerciseExecutionApiV1WorkoutsWorkoutIdExerciseExecutionsExerciseIdPut as jest.Mock).mockReturnValue(mockUpsertExecution)
  ;(useReorderExercisesApiV1WorkoutsWorkoutIdExerciseExecutionsReorderPatch as jest.Mock).mockReturnValue(mockReorderExercises)

  return {
    mockWorkoutStore,
    mockUIStore,
    mockSession,
    mockCacheUtils,
    mockFinishWorkout,
    mockUpsertExecution,
    mockReorderExercises,
  }
}

export const clearAllMocks = () => {
  jest.clearAllMocks()
}

// Custom render function that wraps components with necessary providers if needed
export const renderWithProviders = (
  ui: ReactElement,
  options?: Omit<RenderOptions, 'wrapper'>
) => {
  return render(ui, options)
}

// Common test assertions
export const expectMutationToHaveBeenCalledWith = (
  mutation: MockMutation,
  expectedArgs: any
) => {
  expect(mutation.mutateAsync).toHaveBeenCalledWith(expectedArgs)
}

export const expectStoreActionToHaveBeenCalledWith = (
  storeAction: jest.Mock,
  expectedArgs: any
) => {
  expect(storeAction).toHaveBeenCalledWith(expectedArgs)
}
