import { create } from 'zustand'
import type { WorkoutResponse, ExerciseExecutionResponse, SetResponse } from '@/lib/api/model'
import { generateOptimisticId, isOptimisticId, createOptimisticExerciseExecution, createOptimisticSet, type OptimisticExerciseExecution, type OptimisticSet, type PendingOperation } from '@/lib/utils/optimistic'
import { toast } from 'sonner'

interface WorkoutState {
  // Active workout
  activeWorkout: WorkoutResponse | null
  workoutTimer: number
  timerInterval: NodeJS.Timeout | null

  // Pending operations for dependent operations
  pendingOperations: PendingOperation[]

  // Workout actions
  setActiveWorkout: (workout: WorkoutResponse | null) => void
  updateWorkoutTimer: () => void
  startTimer: () => void
  stopTimer: () => void
  resetTimer: () => void

  // Exercise management
  addExerciseToWorkout: (exercise: ExerciseExecutionResponse) => void
  updateExerciseInWorkout: (exercise: ExerciseExecutionResponse) => void
  removeExerciseFromWorkout: (exerciseId: number) => void
  reorderExercises: (exercises: ExerciseExecutionResponse[]) => void

  // Optimistic updates for exercises
  addOptimisticExercise: (exercise: { id: number; name: string; body_part: string; modality: string }) => string
  reconcileExerciseExecution: (optimisticId: string, serverData: ExerciseExecutionResponse) => void
  removeOptimisticExercise: (optimisticId: string) => void
  cleanupFailedOperations: (optimisticId: string) => void

  // Optimistic updates for sets
  addOptimisticSet: (exerciseId: number | string, setData: { weight: number; clean_reps: number; forced_reps: number; note_text?: string }) => string
  reconcileSet: (optimisticId: string, serverData: SetResponse) => void
  removeOptimisticSet: (optimisticId: string) => void
  cleanupFailedSetOperation: (optimisticId: string) => void

  // Operation queue management
  addPendingOperation: (operation: PendingOperation) => void
  processPendingOperations: (dependencyId: string) => void
  removePendingOperation: (operationId: string) => void
}

export const useWorkoutStore = create<WorkoutState>((set, get) => ({
  // Initial state
  activeWorkout: null,
  workoutTimer: 0,
  timerInterval: null,
  pendingOperations: [],

  // Actions
  setActiveWorkout: (workout) => set({ activeWorkout: workout }),

  updateWorkoutTimer: () => set((state) => ({ workoutTimer: state.workoutTimer + 1 })),

  startTimer: () => {
    const { timerInterval, stopTimer } = get()
    if (timerInterval) stopTimer()

    const interval = setInterval(() => {
      get().updateWorkoutTimer()
    }, 1000)

    set({ timerInterval: interval })
  },

  stopTimer: () => {
    const { timerInterval } = get()
    if (timerInterval) {
      clearInterval(timerInterval)
      set({ timerInterval: null })
    }
  },

  resetTimer: () => {
    const { stopTimer } = get()
    stopTimer()
    set({ workoutTimer: 0 })
  },

  addExerciseToWorkout: (exercise) =>
    set((state) => ({
      activeWorkout: state.activeWorkout
        ? {
            ...state.activeWorkout,
            exercise_executions: [...(state.activeWorkout.exercise_executions || []), exercise],
          }
        : null,
    })),

  // Optimistic exercise addition
  addOptimisticExercise: (exercise) => {
    const optimisticId = generateOptimisticId()
    const exerciseOrder = (get().activeWorkout?.exercise_executions?.length || 0) + 1

    const optimisticExecution = createOptimisticExerciseExecution(exercise, exerciseOrder)

    set((state) => ({
      activeWorkout: state.activeWorkout
        ? {
            ...state.activeWorkout,
            exercise_executions: [...(state.activeWorkout.exercise_executions || []), optimisticExecution as any],
          }
        : null,
    }))

    return optimisticId
  },

  // Reconcile optimistic data with server response
  reconcileExerciseExecution: (optimisticId, serverData) => {
    set((state) => ({
      activeWorkout: state.activeWorkout
        ? {
            ...state.activeWorkout,
            exercise_executions: state.activeWorkout.exercise_executions?.map((ex) =>
              (ex as any).id === optimisticId ? serverData : ex
            ),
          }
        : null,
    }))

    // Process any pending operations that were waiting for this exercise
    get().processPendingOperations(optimisticId)
  },

  // Remove optimistic exercise (on failure)
  removeOptimisticExercise: (optimisticId) =>
    set((state) => ({
      activeWorkout: state.activeWorkout
        ? {
            ...state.activeWorkout,
            exercise_executions: state.activeWorkout.exercise_executions?.filter(
              (ex) => (ex as any).id !== optimisticId
            ),
          }
        : null,
    })),

  // Cleanup failed operations and notify user
  cleanupFailedOperations: (optimisticId) => {
    get().removeOptimisticExercise(optimisticId)
    toast.error('Exercise couldn\'t be added', {
      duration: 3000,
      position: 'bottom-right'
    })
  },

  updateExerciseInWorkout: (updatedExercise) =>
    set((state) => ({
      activeWorkout: state.activeWorkout
        ? {
            ...state.activeWorkout,
            exercise_executions: state.activeWorkout.exercise_executions?.map((ex) =>
              ex.exercise_id === updatedExercise.exercise_id ? updatedExercise : ex
            ),
          }
        : null,
    })),

  removeExerciseFromWorkout: (exerciseId) =>
    set((state) => ({
      activeWorkout: state.activeWorkout
        ? {
            ...state.activeWorkout,
            exercise_executions: state.activeWorkout.exercise_executions?.filter(
              (ex) => ex.exercise_id !== exerciseId
            ),
          }
        : null,
    })),

  reorderExercises: (exercises) =>
    set((state) => ({
      activeWorkout: state.activeWorkout
        ? {
            ...state.activeWorkout,
            exercise_executions: exercises,
          }
        : null,
    })),

  // Optimistic set operations
  addOptimisticSet: (exerciseId, setData) => {
    const optimisticId = generateOptimisticId()
    const optimisticSet = createOptimisticSet(setData, optimisticId)

    set((state) => ({
      activeWorkout: state.activeWorkout
        ? {
            ...state.activeWorkout,
            exercise_executions: state.activeWorkout.exercise_executions?.map((ex) => {
              // Handle both numeric and string IDs (for optimistic exercises)
              const exId = (ex as any).id || ex.exercise_id
              const targetId = exerciseId

              if (exId === targetId || ex.exercise_id === exerciseId) {
                return {
                  ...ex,
                  sets: [...(ex.sets || []), optimisticSet as any],
                }
              }
              return ex
            }),
          }
        : null,
    }))

    return optimisticId
  },

  reconcileSet: (optimisticId, serverData) =>
    set((state) => ({
      activeWorkout: state.activeWorkout
        ? {
            ...state.activeWorkout,
            exercise_executions: state.activeWorkout.exercise_executions?.map((ex) => ({
              ...ex,
              sets: ex.sets?.map((set: any) =>
                set.id === optimisticId ? serverData : set
              ),
            })),
          }
        : null,
    })),

  removeOptimisticSet: (optimisticId) =>
    set((state) => ({
      activeWorkout: state.activeWorkout
        ? {
            ...state.activeWorkout,
            exercise_executions: state.activeWorkout.exercise_executions?.map((ex) => ({
              ...ex,
              sets: ex.sets?.filter((set: any) => set.id !== optimisticId),
            })),
          }
        : null,
    })),

  cleanupFailedSetOperation: (optimisticId) => {
    get().removeOptimisticSet(optimisticId)
    toast.error('Set couldn\'t be added', {
      duration: 3000,
      position: 'bottom-right'
    })
  },

  // Operation queue management
  addPendingOperation: (operation) =>
    set((state) => ({
      pendingOperations: [...state.pendingOperations, operation],
    })),

  processPendingOperations: (dependencyId) => {
    const { pendingOperations } = get()
    const readyOperations = pendingOperations.filter(op => op.dependsOn === dependencyId)

    readyOperations.forEach(async (operation) => {
      try {
        await operation.execute()
        get().removePendingOperation(operation.id)
      } catch (error) {
        operation.rollback()
        get().removePendingOperation(operation.id)
      }
    })
  },

  removePendingOperation: (operationId) =>
    set((state) => ({
      pendingOperations: state.pendingOperations.filter(op => op.id !== operationId),
    })),
}))
