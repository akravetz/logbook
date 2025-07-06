import { renderHook, act } from '@testing-library/react'
import { useWorkoutStore } from './workout-store'
import { createMockWorkout, createMockExerciseExecution } from '@/lib/test-factories'

// Mock the optimistic utils to control ID generation for testing
jest.mock('@/lib/utils/optimistic', () => {
  let idCounter = 0
  return {
    generateOptimisticId: () => `temp-${++idCounter}`,
    isOptimisticId: (id: string | number) => typeof id === 'string' && id.startsWith('temp-'),
    createOptimisticExerciseExecution: jest.fn(),
    createOptimisticSet: jest.requireActual('@/lib/utils/optimistic').createOptimisticSet,
    createPendingOperation: jest.fn(),
  }
})

// Mock sonner toast
jest.mock('sonner', () => ({
  toast: {
    error: jest.fn(),
    success: jest.fn()
  }
}))

describe('WorkoutStore - Optimistic Set Operations', () => {
  beforeEach(() => {
    // Reset the store state before each test
    const { result } = renderHook(() => useWorkoutStore())
    act(() => {
      result.current.setActiveWorkout(null)
    })
    jest.clearAllMocks()
  })

  describe('addOptimisticSet', () => {
    it('should return the same ID that is actually used in the created set', () => {
      const { result } = renderHook(() => useWorkoutStore())

      // Setup: Create a workout with an exercise
      const mockExercise = createMockExerciseExecution({
        exercise_id: 1,
        exercise_name: 'Bench Press',
        sets: []
      })
      const mockWorkout = createMockWorkout({
        id: 1,
        exercise_executions: [mockExercise]
      })

      act(() => {
        result.current.setActiveWorkout(mockWorkout)
      })

      // Test: Add optimistic set
      let returnedId: string
      act(() => {
        returnedId = result.current.addOptimisticSet(1, {
          weight: 100,
          clean_reps: 10,
          forced_reps: 0
        })
      })

      // Assertion: The returned ID should match the ID of the set that was actually added
      const currentWorkout = result.current.activeWorkout
      const updatedExercise = currentWorkout?.exercise_executions?.find(ex => ex.exercise_id === 1)
      const addedSet = updatedExercise?.sets?.[0]

      expect(addedSet).toBeDefined()
      expect(addedSet?.id).toBe(returnedId!)
      expect(returnedId!).toMatch(/^temp-\d+$/) // Should be an optimistic ID
    })

    it('should allow reconciling the set using the returned ID', () => {
      const { result } = renderHook(() => useWorkoutStore())

      // Setup: Create a workout with an exercise
      const mockExercise = createMockExerciseExecution({
        exercise_id: 1,
        exercise_name: 'Bench Press',
        sets: []
      })
      const mockWorkout = createMockWorkout({
        id: 1,
        exercise_executions: [mockExercise]
      })

      act(() => {
        result.current.setActiveWorkout(mockWorkout)
      })

      // Add optimistic set
      let optimisticId: string
      act(() => {
        optimisticId = result.current.addOptimisticSet(1, {
          weight: 100,
          clean_reps: 10,
          forced_reps: 0
        })
      })

      // Verify set was added
      let currentWorkout = result.current.activeWorkout
      let updatedExercise = currentWorkout?.exercise_executions?.find(ex => ex.exercise_id === 1)
      expect(updatedExercise?.sets).toHaveLength(1)
      expect(updatedExercise?.sets?.[0]?.id).toBe(optimisticId!)

      // Now reconcile with server data
      const serverSetData = {
        id: 123, // Real server ID
        weight: 100,
        clean_reps: 10,
        forced_reps: 0,
        note_text: '',
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString()
      }

      act(() => {
        result.current.reconcileSet(optimisticId!, serverSetData)
      })

      // Verify reconciliation worked
      currentWorkout = result.current.activeWorkout
      updatedExercise = currentWorkout?.exercise_executions?.find(ex => ex.exercise_id === 1)
      expect(updatedExercise?.sets).toHaveLength(1)
      expect(updatedExercise?.sets?.[0]?.id).toBe(123) // Should now have server ID
      expect(updatedExercise?.sets?.[0]?.weight).toBe(100)
    })

    it('should fail reconciliation if IDs do not match (demonstrating the bug)', () => {
      const { result } = renderHook(() => useWorkoutStore())

      // Setup: Create a workout with an exercise
      const mockExercise = createMockExerciseExecution({
        exercise_id: 1,
        exercise_name: 'Bench Press',
        sets: []
      })
      const mockWorkout = createMockWorkout({
        id: 1,
        exercise_executions: [mockExercise]
      })

      act(() => {
        result.current.setActiveWorkout(mockWorkout)
      })

      // Add optimistic set
      let optimisticId: string
      act(() => {
        optimisticId = result.current.addOptimisticSet(1, {
          weight: 100,
          clean_reps: 10,
          forced_reps: 0
        })
      })

      // Verify set was added
      let currentWorkout = result.current.activeWorkout
      let updatedExercise = currentWorkout?.exercise_executions?.find(ex => ex.exercise_id === 1)
      expect(updatedExercise?.sets).toHaveLength(1)

      // Now try to reconcile with a WRONG ID (simulating the current bug)
      const serverSetData = {
        id: 123,
        weight: 100,
        clean_reps: 10,
        forced_reps: 0,
        note_text: '',
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString()
      }

      const wrongId = 'temp-999' // Wrong optimistic ID
      act(() => {
        result.current.reconcileSet(wrongId, serverSetData)
      })

      // The reconciliation should fail - set should still have optimistic ID
      currentWorkout = result.current.activeWorkout
      updatedExercise = currentWorkout?.exercise_executions?.find(ex => ex.exercise_id === 1)
      expect(updatedExercise?.sets).toHaveLength(1)

      // This test demonstrates the bug: reconciliation fails when IDs don't match
      const setAfterReconciliation = updatedExercise?.sets?.[0]
      expect(setAfterReconciliation?.id).not.toBe(123) // Should still be optimistic ID
      expect(setAfterReconciliation?.id).toMatch(/^temp-/) // Still optimistic
    })
  })
})
