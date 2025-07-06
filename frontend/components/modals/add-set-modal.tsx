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
import { useOptimisticMutation } from '@/lib/hooks/use-optimistic-mutation'
import type { SetCreate } from '@/lib/api/model'
import { logger } from '@/lib/logger'
import { isOptimisticId } from '@/lib/utils/optimistic'

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

  // Optimistic set creation mutation
  const addSetMutation = useOptimisticMutation({
    addOptimistic: (data: { workoutId: number; exerciseId: number; data: SetCreate }) => {
      const optimisticId = addOptimisticSet(data.exerciseId, data.data)
      return optimisticId
    },
    reconcile: (optimisticId: string, serverData: any) => {
      reconcileSet(optimisticId, serverData)
    },
    cleanup: (optimisticId: string) => {
      cleanupFailedSetOperation(optimisticId)
    },
    mutation: createSetMutation,
    getDependency: (data: { workoutId: number; exerciseId: number; data: SetCreate }) => {
      // Find the exercise to check if it's optimistic
      const targetExercise = activeWorkout?.exercise_executions?.find(ex =>
        ex.exercise_id === data.exerciseId || (ex as any).id === data.exerciseId
      )

      // Return the exercise ID if it's optimistic (for dependency queueing)
      if (targetExercise && isOptimisticId((targetExercise as any).id)) {
        return (targetExercise as any).id
      }
      return null
    },
    addPendingOperation,
    onSuccess: () => 'Set added successfully',
    onError: () => 'Failed to add set'
  })

  const onSubmit = async (data: FormData) => {
    if (!activeWorkout?.id || !modals.addSet.exerciseId) return

    const setData: SetCreate = {
      weight: data.weight,
      clean_reps: data.clean_reps,
      forced_reps: data.forced_reps,
    }

    // Close modal immediately (no waiting)
    reset()
    closeAllModals()

    // Use optimistic mutation hook
    await addSetMutation.execute({
      workoutId: activeWorkout.id,
      exerciseId: modals.addSet.exerciseId,
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
