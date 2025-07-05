import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { useSession } from 'next-auth/react'
import { useRouter } from 'next/navigation'
import { useWorkoutStore } from '@/lib/stores/workout-store'
import { useUIStore } from '@/lib/stores/ui-store'
import { useCacheUtils } from '@/lib/cache-tags'
import {
  useFinishWorkoutApiV1WorkoutsWorkoutIdFinishPatch,
  useUpsertExerciseExecutionApiV1WorkoutsWorkoutIdExerciseExecutionsExerciseIdPut,
  useReorderExercisesApiV1WorkoutsWorkoutIdExerciseExecutionsReorderPatch
} from '@/lib/api/generated'
import { ActiveWorkoutScreen } from './active-workout-screen'
import {
  setupActiveWorkoutTest,
  clearAllMocks,
  expectMutationToHaveBeenCalledWith,
} from '@/lib/test-utils'
import {
  createActiveWorkoutWithExercises,
  createFinishedWorkout,
  createEmptyWorkout,
  createMockSet,
  createMockExerciseExecution
} from '@/lib/test-factories'

// Mock all dependencies
jest.mock('next-auth/react')
jest.mock('next/navigation')
jest.mock('@/lib/stores/workout-store')
jest.mock('@/lib/stores/ui-store')
jest.mock('@/lib/cache-tags')
jest.mock('@/lib/api/generated')

const mockRouter = {
  push: jest.fn(),
  replace: jest.fn(),
  back: jest.fn(),
  forward: jest.fn(),
  refresh: jest.fn(),
}

describe('ActiveWorkoutScreen', () => {
  beforeEach(() => {
    clearAllMocks()
    ;(useRouter as jest.Mock).mockReturnValue(mockRouter)
  })

  describe('Basic Rendering', () => {
    it('renders active workout screen with user name', () => {
      setupActiveWorkoutTest({
        workoutState: {
          activeWorkout: createActiveWorkoutWithExercises(1),
          workoutTimer: 120, // 2 minutes
        },
        sessionState: {
          user: { name: 'John Doe' },
        },
      })

      render(<ActiveWorkoutScreen workoutId={1} />)

      expect(screen.getByText('John')).toBeInTheDocument()
      expect(screen.getByText('Active Workout')).toBeInTheDocument()
      expect(screen.getByText('2:00')).toBeInTheDocument() // Timer display
    })

    it('renders exercises with sets', () => {
      const workout = createActiveWorkoutWithExercises(2)
      setupActiveWorkoutTest({
        workoutState: {
          activeWorkout: workout,
        },
      })

      render(<ActiveWorkoutScreen workoutId={1} />)

      expect(screen.getByText('Exercise 1')).toBeInTheDocument()
      expect(screen.getByText('Exercise 2')).toBeInTheDocument()
      // Exercise 1: 135lb and 145lb sets, Exercise 2: 145lb and 155lb sets
      expect(screen.getByText(/135 lb × 8 reps/)).toBeInTheDocument()
      expect(screen.getAllByText(/145 lb × 8 reps/)).toHaveLength(2) // Both exercises have a 145lb set
      expect(screen.getByText(/155 lb × 8 reps/)).toBeInTheDocument()
    })

    it('renders empty state with add exercise button', () => {
      setupActiveWorkoutTest({
        workoutState: {
          activeWorkout: createEmptyWorkout(),
        },
      })

      render(<ActiveWorkoutScreen workoutId={1} />)

      expect(screen.getByText('Add Exercise')).toBeInTheDocument()
    })
  })

  describe('Finish Workout Flow', () => {
    it('successfully finishes workout and navigates home', async () => {
      const user = userEvent.setup()
      const { mockFinishWorkout, mockCacheUtils, mockWorkoutStore } = setupActiveWorkoutTest({
        workoutState: {
          activeWorkout: createActiveWorkoutWithExercises(1),
        },
      })

      mockFinishWorkout.mutateAsync.mockResolvedValue({ deleted: false })

      render(<ActiveWorkoutScreen workoutId={1} />)

      const finishButton = screen.getByRole('button', { name: /finish/i })
      await user.click(finishButton)

      await waitFor(() => {
        expectMutationToHaveBeenCalledWith(mockFinishWorkout, { workoutId: 1 })
        expect(mockCacheUtils.invalidateWorkoutData).toHaveBeenCalled()
        expect(mockWorkoutStore.stopTimer).toHaveBeenCalled()
        expect(mockWorkoutStore.resetTimer).toHaveBeenCalled()
        expect(mockWorkoutStore.setActiveWorkout).toHaveBeenCalledWith(null)
        expect(mockRouter.push).toHaveBeenCalledWith('/')
      })
    })

    it('handles empty workout deletion', async () => {
      const user = userEvent.setup()
      const { mockFinishWorkout } = setupActiveWorkoutTest({
        workoutState: {
          activeWorkout: createEmptyWorkout(),
        },
      })

      mockFinishWorkout.mutateAsync.mockResolvedValue({ deleted: true })

      render(<ActiveWorkoutScreen workoutId={1} />)

      const finishButton = screen.getByRole('button', { name: /finish/i })
      await user.click(finishButton)

      await waitFor(() => {
        expect(mockRouter.push).toHaveBeenCalledWith('/')
      })
    })

    it('shows loading state during finish', async () => {
      setupActiveWorkoutTest({
        workoutState: {
          activeWorkout: createActiveWorkoutWithExercises(1),
        },
        apiMocks: {
          finishWorkout: { isPending: true },
        },
      })

      render(<ActiveWorkoutScreen workoutId={1} />)

      expect(screen.getByRole('button', { name: /finishing/i })).toBeInTheDocument()
      expect(screen.getByRole('button', { name: /finishing/i })).toBeDisabled()
    })

    it('hides finish button for finished workouts', () => {
      setupActiveWorkoutTest({
        workoutState: {
          activeWorkout: createFinishedWorkout(),
        },
      })

      render(<ActiveWorkoutScreen workoutId={1} />)

      expect(screen.queryByRole('button', { name: /finish/i })).not.toBeInTheDocument()
    })
  })

  describe('Delete Set Flow', () => {
    it('successfully deletes a set', async () => {
      const user = userEvent.setup()
      const workout = createActiveWorkoutWithExercises(1)
      const exercise = workout.exercise_executions![0]

      const { mockUpsertExecution, mockCacheUtils, mockWorkoutStore } = setupActiveWorkoutTest({
        workoutState: {
          activeWorkout: workout,
        },
      })

      const updatedExecution = {
        ...exercise,
        sets: exercise.sets!.slice(1), // Remove first set
      }
      mockUpsertExecution.mutateAsync.mockResolvedValue(updatedExecution)

      render(<ActiveWorkoutScreen workoutId={1} />)

      // Find the delete button using semantic aria-label
      const deleteButton = screen.getByRole('button', { name: /delete set 1 for exercise 1/i })
      await user.click(deleteButton)

      await waitFor(() => {
        expectMutationToHaveBeenCalledWith(mockUpsertExecution, {
          workoutId: 1,
          exerciseId: exercise.exercise_id,
          data: {
            sets: [
              {
                weight: exercise.sets![1].weight,
                clean_reps: exercise.sets![1].clean_reps,
                forced_reps: exercise.sets![1].forced_reps,
                note_text: exercise.sets![1].note_text,
              },
            ],
            exercise_order: exercise.exercise_order,
            note_text: exercise.note_text,
          },
        })
        expect(mockCacheUtils.invalidateWorkoutData).toHaveBeenCalled()
        expect(mockWorkoutStore.updateExerciseInWorkout).toHaveBeenCalledWith(updatedExecution)
      })
    })

    it('prevents deletion for finished workouts', () => {
      setupActiveWorkoutTest({
        workoutState: {
          activeWorkout: createFinishedWorkout(),
        },
      })

      render(<ActiveWorkoutScreen workoutId={1} />)

      // Delete/Edit buttons should not be present for finished workouts
      expect(screen.queryByRole('button', { name: /edit set/i })).not.toBeInTheDocument()
    })
  })

  describe('Modal Interactions', () => {
    it('opens add exercise modal', async () => {
      const user = userEvent.setup()
      const { mockUIStore } = setupActiveWorkoutTest({
        workoutState: {
          activeWorkout: createEmptyWorkout(),
        },
      })

      render(<ActiveWorkoutScreen workoutId={1} />)

      const addExerciseButton = screen.getByRole('button', { name: /add exercise to workout/i })
      await user.click(addExerciseButton)

      expect(mockUIStore.openSelectExerciseModal).toHaveBeenCalled()
    })

    it('opens add set modal', async () => {
      const user = userEvent.setup()
      const workout = createActiveWorkoutWithExercises(1)
      const { mockUIStore } = setupActiveWorkoutTest({
        workoutState: {
          activeWorkout: workout,
        },
      })

      render(<ActiveWorkoutScreen workoutId={1} />)

      const addSetButton = screen.getByRole('button', { name: /add set to exercise 1/i })
      await user.click(addSetButton)

      expect(mockUIStore.openAddSetModal).toHaveBeenCalledWith(
        workout.exercise_executions![0].exercise_id,
        {
          id: workout.exercise_executions![0].exercise_id,
          name: workout.exercise_executions![0].exercise_name,
          body_part: workout.exercise_executions![0].exercise_body_part,
          modality: workout.exercise_executions![0].exercise_modality,
        }
      )
    })

    it('opens edit set modal', async () => {
      const user = userEvent.setup()
      const workout = createActiveWorkoutWithExercises(1)
      const { mockUIStore } = setupActiveWorkoutTest({
        workoutState: {
          activeWorkout: workout,
        },
      })

      render(<ActiveWorkoutScreen workoutId={1} />)

      const editButton = screen.getByRole('button', { name: /edit set 1 for exercise 1/i })
      await user.click(editButton)

      expect(mockUIStore.openEditSetModal).toHaveBeenCalledWith(
        workout.exercise_executions![0].exercise_id,
        workout.exercise_executions![0].sets![0].id,
        workout.exercise_executions![0].sets![0]
      )
    })

    it('opens voice note modal', async () => {
      const user = userEvent.setup()
      const workout = createActiveWorkoutWithExercises(1)
      const { mockUIStore } = setupActiveWorkoutTest({
        workoutState: {
          activeWorkout: workout,
        },
      })

      render(<ActiveWorkoutScreen workoutId={1} />)

      // Find voice button using semantic aria-label
      const voiceButton = screen.getByRole('button', { name: /add voice note for exercise 1/i })
      await user.click(voiceButton)

      expect(mockUIStore.openVoiceNoteModal).toHaveBeenCalledWith(
        workout.exercise_executions![0].exercise_id,
        workout.exercise_executions![0].exercise_name
      )
    })
  })

  describe('Timer Display', () => {
    it('formats timer correctly', () => {
      setupActiveWorkoutTest({
        workoutState: {
          activeWorkout: createActiveWorkoutWithExercises(1),
          workoutTimer: 3661, // 1 hour, 1 minute, 1 second
        },
      })

      render(<ActiveWorkoutScreen workoutId={1} />)

      expect(screen.getByText('61:01')).toBeInTheDocument()
    })
  })

  describe('Exercise Display', () => {
    it('shows exercise notes', () => {
      const exercise = createMockExerciseExecution({
        note_text: 'Remember to keep back straight',
      })
      const workout = createActiveWorkoutWithExercises(0)
      workout.exercise_executions = [exercise]

      setupActiveWorkoutTest({
        workoutState: {
          activeWorkout: workout,
        },
      })

      render(<ActiveWorkoutScreen workoutId={1} />)

      expect(screen.getByText('Note: Remember to keep back straight')).toBeInTheDocument()
    })

    it('shows forced reps correctly', () => {
      const setWithForcedReps = createMockSet({
        clean_reps: 8,
        forced_reps: 2,
        weight: 135,
      })
      const exercise = createMockExerciseExecution({
        sets: [setWithForcedReps],
      })
      const workout = createActiveWorkoutWithExercises(0)
      workout.exercise_executions = [exercise]

      setupActiveWorkoutTest({
        workoutState: {
          activeWorkout: workout,
        },
      })

      render(<ActiveWorkoutScreen workoutId={1} />)

      expect(screen.getByText('135 lb × 8 reps + 2')).toBeInTheDocument()
    })

    it('disables interactions for finished workouts', () => {
      setupActiveWorkoutTest({
        workoutState: {
          activeWorkout: createFinishedWorkout(),
        },
      })

      render(<ActiveWorkoutScreen workoutId={1} />)

      // Drag handle should be disabled
      const dragHandle = screen.getByLabelText(/drag to reorder/i)
      expect(dragHandle).toBeDisabled()

      // Action buttons should not be present
      expect(screen.queryByRole('button', { name: /add set/i })).not.toBeInTheDocument()
      expect(screen.queryByRole('button', { name: /add exercise/i })).not.toBeInTheDocument()
    })
  })

  describe('Error Handling', () => {
    it('handles finish workout API errors gracefully', async () => {
      const user = userEvent.setup()

      const { mockFinishWorkout } = setupActiveWorkoutTest({
        workoutState: {
          activeWorkout: createActiveWorkoutWithExercises(1),
        },
      })

      mockFinishWorkout.mutateAsync.mockRejectedValue(new Error('API Error'))

      render(<ActiveWorkoutScreen workoutId={1} />)

      const finishButton = screen.getByRole('button', { name: /finish/i })
      await user.click(finishButton)

      // Verify that the mutation was called and failed
      await waitFor(() => {
        expect(mockFinishWorkout.mutateAsync).toHaveBeenCalledWith({ workoutId: 1 })
      })

      // The button should still be present (not navigated away due to error)
      expect(screen.getByRole('button', { name: /finish/i })).toBeInTheDocument()
    })
  })
})
