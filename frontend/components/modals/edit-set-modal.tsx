"use client"

import { useEffect } from 'react'
import { useForm } from 'react-hook-form'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from '@/components/ui/modal'
import { ChevronUp, ChevronDown } from 'lucide-react'
import { useUIStore } from '@/lib/stores/ui-store'
import { useWorkoutStore } from '@/lib/stores/workout-store'
import {
  useUpdateSetApiV1WorkoutsWorkoutIdExerciseExecutionsExerciseIdSetsSetIdPatch,
  useGetExerciseExecutionApiV1WorkoutsWorkoutIdExerciseExecutionsExerciseIdGet
} from '@/lib/api/generated'
import { useOptimisticMutation } from '@/lib/hooks/use-optimistic-mutation'
import type { SetUpdate } from '@/lib/api/model'

interface FormData {
  weight: number
  clean_reps: number
  forced_reps: number
}

export function EditSetModal() {
  const { modals, closeAllModals } = useUIStore()
  const { activeWorkout, updateExerciseInWorkout } = useWorkoutStore()

  const { register, handleSubmit, watch, setValue, reset } = useForm<FormData>()

  const updateSetMutation = useUpdateSetApiV1WorkoutsWorkoutIdExerciseExecutionsExerciseIdSetsSetIdPatch()

  // Refetch exercise execution after updating set
  const { refetch: refetchExecution } = useGetExerciseExecutionApiV1WorkoutsWorkoutIdExerciseExecutionsExerciseIdGet(
    activeWorkout?.id || 0,
    modals.editSet.exerciseId || 0,
    {
      query: {
        enabled: false,
      }
    }
  )

  // Optimistic set update mutation
  const editSetMutation = useOptimisticMutation({
    addOptimistic: (data: { workoutId: number; exerciseId: number; setId: number; data: SetUpdate }) => {
      // For set updates, we optimistically update the set data in the local state
      if (!activeWorkout) return 'temp-set-update'

      const exercise = activeWorkout.exercise_executions?.find(ex => ex.exercise_id === data.exerciseId)
      if (exercise) {
        const updatedSets = exercise.sets.map(set =>
          set.id === data.setId ? { ...set, ...data.data } : set
        )
        const updatedExercise = { ...exercise, sets: updatedSets }
        updateExerciseInWorkout(updatedExercise)
      }

      return `set-update-${data.setId}-${Date.now()}`
    },
    reconcile: async (optimisticId: string, serverData: any) => {
      // Refetch the exercise execution to get the updated data from server
      const { data: updatedExecution } = await refetchExecution()
      if (updatedExecution) {
        updateExerciseInWorkout(updatedExecution)
      }
    },
    cleanup: async (optimisticId: string) => {
      // On error, refetch to restore correct state
      const { data: updatedExecution } = await refetchExecution()
      if (updatedExecution) {
        updateExerciseInWorkout(updatedExecution)
      }
    },
    mutation: updateSetMutation,
    onSuccess: () => 'Set updated successfully',
    onError: () => 'Failed to update set'
  })

  // Set form values when modal opens
  useEffect(() => {
    if (modals.editSet.open && modals.editSet.currentData) {
      reset({
        weight: modals.editSet.currentData.weight || 0,
        clean_reps: modals.editSet.currentData.clean_reps || 0,
        forced_reps: modals.editSet.currentData.forced_reps || 0,
      })
    }
  }, [modals.editSet.open, modals.editSet.currentData, reset])

  const onSubmit = async (data: FormData) => {
    if (!activeWorkout?.id || !modals.editSet.exerciseId || !modals.editSet.setId) return

    const setData: SetUpdate = {
      weight: data.weight,
      clean_reps: data.clean_reps,
      forced_reps: data.forced_reps,
    }

    // Close modal immediately (optimistic update)
    reset()
    closeAllModals()

    // Use optimistic mutation hook
    await editSetMutation.execute({
      workoutId: activeWorkout.id,
      exerciseId: modals.editSet.exerciseId,
      setId: modals.editSet.setId,
      data: setData
    })
  }

  const handleClose = () => {
    reset()
    closeAllModals()
  }

  const adjustValue = (field: keyof FormData, increment: number) => {
    const currentValue = watch(field)
    const newValue = Math.max(0, currentValue + increment)
    setValue(field, newValue)
  }

  // Format preview text
  const weight = watch('weight')
  const cleanReps = watch('clean_reps')
  const forcedReps = watch('forced_reps')
  const previewText = `${weight} lb × ${cleanReps} reps${forcedReps > 0 ? ` + ${forcedReps}` : ''}`

  return (
    <Dialog open={modals.editSet.open} onOpenChange={handleClose}>
      <DialogContent className="max-w-md" keyboardAware>
        <DialogHeader>
          <DialogTitle>Edit Set</DialogTitle>
          <DialogDescription>
            Modify the weight and number of reps for this set
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
          {/* Weight */}
          <div>
            <label className="text-base font-medium mb-2 block">
              Weight (lbs)
            </label>
            <div className="relative">
              <input
                {...register('weight', { valueAsNumber: true })}
                type="number"
                step="0.5"
                className="w-full px-4 py-3 pr-12 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-black focus:border-transparent"
              />
              <div className="absolute right-1 top-1 bottom-1 flex flex-col">
                <button
                  type="button"
                  onClick={() => adjustValue('weight', 5)}
                  className="flex-1 px-2 hover:bg-gray-100 rounded"
                >
                  <ChevronUp className="w-4 h-4" />
                </button>
                <button
                  type="button"
                  onClick={() => adjustValue('weight', -5)}
                  className="flex-1 px-2 hover:bg-gray-100 rounded"
                >
                  <ChevronDown className="w-4 h-4" />
                </button>
              </div>
            </div>
          </div>

          {/* Clean Reps */}
          <div>
            <label className="text-base font-medium mb-2 block">
              Clean Reps
            </label>
            <input
              {...register('clean_reps', { valueAsNumber: true })}
              type="number"
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-black focus:border-transparent"
            />
          </div>

          {/* Forced Reps */}
          <div>
            <label className="text-base font-medium mb-2 block">
              Forced Reps
            </label>
            <input
              {...register('forced_reps', { valueAsNumber: true })}
              type="number"
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-black focus:border-transparent"
            />
          </div>

          {/* Preview */}
          <div className="text-center py-2">
            <p className="text-sm text-gray-600">Preview: {previewText}</p>
          </div>

          {/* Actions */}
          <div className="flex gap-3 pt-4">
            <button
              type="button"
              onClick={handleClose}
              className="btn-secondary flex-1"
              disabled={editSetMutation.isExecuting}
            >
              Cancel
            </button>
            <button
              type="submit"
              className="btn-primary flex-1"
              disabled={editSetMutation.isExecuting}
            >
              {editSetMutation.isExecuting ? 'Updating...' : 'Update Set'}
            </button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  )
}
