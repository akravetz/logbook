"use client"

import { useState } from 'react'
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
  useCreateSetApiV1WorkoutsWorkoutIdExerciseExecutionsExerciseIdSetsPost,
  useGetExerciseExecutionApiV1WorkoutsWorkoutIdExerciseExecutionsExerciseIdGet
} from '@/lib/api/generated'
import type { SetCreate } from '@/lib/api/model'
import { logger } from '@/lib/logger'
import { toast } from 'sonner'
import { isOptimisticId, createPendingOperation } from '@/lib/utils/optimistic'

interface FormData {
  weight: number
  clean_reps: number
  forced_reps: number
}

export function AddSetModal() {
  const { modals, closeAllModals, selectedExerciseForSet } = useUIStore()
  const {
    activeWorkout,
    updateExerciseInWorkout,
    addOptimisticSet,
    reconcileSet,
    cleanupFailedSetOperation,
    addPendingOperation
  } = useWorkoutStore()

  const { register, handleSubmit, watch, setValue, reset } = useForm<FormData>({
    defaultValues: {
      weight: 0,
      clean_reps: 0,
      forced_reps: 0,
    }
  })

  const createSetMutation = useCreateSetApiV1WorkoutsWorkoutIdExerciseExecutionsExerciseIdSetsPost()

  // Refetch exercise execution after adding set
  const { refetch: refetchExecution } = useGetExerciseExecutionApiV1WorkoutsWorkoutIdExerciseExecutionsExerciseIdGet(
    activeWorkout?.id || 0,
    modals.addSet.exerciseId || 0,
    {
      query: {
        enabled: false,
      }
    }
  )

  const onSubmit = async (data: FormData) => {
    if (!activeWorkout?.id || !modals.addSet.exerciseId) return

    const setData = {
      weight: data.weight,
      clean_reps: data.clean_reps,
      forced_reps: data.forced_reps,
    }

    const exerciseId = modals.addSet.exerciseId

    // Find the exercise to check if it's optimistic
    const targetExercise = activeWorkout.exercise_executions?.find(ex =>
      ex.exercise_id === exerciseId || (ex as any).id === exerciseId
    )

    // 1. Add optimistic set immediately
    const optimisticId = addOptimisticSet(exerciseId, setData)

    // 2. Close modal immediately (no waiting)
    reset()
    closeAllModals()

    // 3. Handle API call based on whether the exercise is optimistic or not
    if (targetExercise && isOptimisticId((targetExercise as any).id)) {
      // Exercise is still optimistic - queue the set creation
      const pendingOperation = createPendingOperation(
        'ADD_SET',
        { exerciseId, setData, optimisticId },
        async () => {
          // This will execute once the exercise is reconciled
          const realExerciseId = targetExercise.exercise_id
          const serverResponse = await createSetMutation.mutateAsync({
            workoutId: activeWorkout.id,
            exerciseId: realExerciseId,
            data: setData,
          })
          reconcileSet(optimisticId, serverResponse)
          toast.success('Set added successfully')
        },
        () => {
          // Rollback on failure
          cleanupFailedSetOperation(optimisticId)
        },
        (targetExercise as any).id // Depends on the optimistic exercise ID
      )

      addPendingOperation(pendingOperation)
    } else {
      // Exercise is real - make API call immediately
      createSetMutation.mutateAsync({
        workoutId: activeWorkout.id,
        exerciseId: exerciseId as number,
        data: setData,
      }).then(async (serverResponse) => {
        reconcileSet(optimisticId, serverResponse)
        toast.success('Set added successfully')
      }).catch((error) => {
        logger.error('Failed to create set:', error)
        cleanupFailedSetOperation(optimisticId)
      })
    }
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
    <Dialog open={modals.addSet.open} onOpenChange={handleClose}>
      <DialogContent className="max-w-md" keyboardAware>
        <DialogHeader>
          <DialogTitle>Add Set</DialogTitle>
          <DialogDescription>
            Enter the weight and number of reps for this set
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
            >
              Cancel
            </button>
            <button
              type="submit"
              className="btn-primary flex-1"
              disabled={weight === 0 && cleanReps === 0}
            >
              Add Set
            </button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  )
}
