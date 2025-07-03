import { create } from 'zustand'
import type { WorkoutResponse, ExerciseExecutionResponse } from '@/lib/api/model'

interface WorkoutState {
  // Active workout
  activeWorkout: WorkoutResponse | null
  workoutTimer: number
  timerInterval: NodeJS.Timeout | null

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
}

export const useWorkoutStore = create<WorkoutState>((set, get) => ({
  // Initial state
  activeWorkout: null,
  workoutTimer: 0,
  timerInterval: null,

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
}))
