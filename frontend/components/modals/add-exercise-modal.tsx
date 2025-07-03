"use client"

import { useState } from 'react'
import { useForm } from 'react-hook-form'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/modal'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { useUIStore } from '@/lib/stores/ui-store'
import { useWorkoutStore } from '@/lib/stores/workout-store'
import {
  useCreateExerciseApiV1ExercisesPost,
  useUpsertExerciseExecutionApiV1WorkoutsWorkoutIdExerciseExecutionsExerciseIdPut
} from '@/lib/api/generated'
import type { ExerciseCreate, ExerciseExecutionRequest, ExerciseModality } from '@/lib/api/model'

interface FormData {
  name: string
  body_part: string
  modality: ExerciseModality
}

const bodyParts = [
  { value: 'chest', label: 'Chest' },
  { value: 'back', label: 'Back' },
  { value: 'shoulders', label: 'Shoulders' },
  { value: 'arms', label: 'Arms' },
  { value: 'legs', label: 'Legs' },
  { value: 'core', label: 'Core' },
  { value: 'full_body', label: 'Full Body' },
]

const modalities = [
  { value: 'DUMBBELL' as ExerciseModality, label: 'Dumbbell' },
  { value: 'BARBELL' as ExerciseModality, label: 'Barbell' },
  { value: 'CABLE' as ExerciseModality, label: 'Cable' },
  { value: 'MACHINE' as ExerciseModality, label: 'Machine' },
  { value: 'SMITH' as ExerciseModality, label: 'Smith Machine' },
  { value: 'BODYWEIGHT' as ExerciseModality, label: 'Bodyweight' },
]

export function AddExerciseModal() {
  const { modals, closeAllModals } = useUIStore()
  const { activeWorkout, addExerciseToWorkout } = useWorkoutStore()
  const [isSubmitting, setIsSubmitting] = useState(false)

  const { register, handleSubmit, formState: { errors }, setValue, watch, reset } = useForm<FormData>()

  const createExerciseMutation = useCreateExerciseApiV1ExercisesPost()
  const upsertExecutionMutation = useUpsertExerciseExecutionApiV1WorkoutsWorkoutIdExerciseExecutionsExerciseIdPut()

  const onSubmit = async (data: FormData) => {
    if (!activeWorkout?.id) return

    setIsSubmitting(true)

    try {
      // Create the exercise
      const exerciseData: ExerciseCreate = {
        name: data.name,
        body_part: data.body_part,
        modality: data.modality,
      }

      const exerciseResult = await createExerciseMutation.mutateAsync({ data: exerciseData })

      // Add to workout
      const executionData: ExerciseExecutionRequest = {
        sets: [],
        exercise_order: (activeWorkout.exercise_executions?.length || 0) + 1,
      }

      const executionResult = await upsertExecutionMutation.mutateAsync({
        workoutId: activeWorkout.id,
        exerciseId: exerciseResult.id,
        data: executionData,
      })

      // Update local state
      addExerciseToWorkout(executionResult)

      // Reset form and close modal
      reset()
      closeAllModals()
    } catch (error) {
      console.error('Failed to create exercise:', error)
    } finally {
      setIsSubmitting(false)
    }
  }

  const handleClose = () => {
    reset()
    closeAllModals()
  }

  return (
    <Dialog open={modals.addExercise} onOpenChange={handleClose}>
      <DialogContent className="max-w-md">
        <DialogHeader>
          <DialogTitle>Add New Exercise</DialogTitle>
        </DialogHeader>

        <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
          {/* Exercise Name */}
          <div>
            <label className="text-base font-medium mb-2 block">
              Exercise Name
            </label>
            <input
              {...register('name', { required: 'Exercise name is required' })}
              placeholder="e.g., Bench Press"
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-black focus:border-transparent"
              autoFocus
            />
            {errors.name && (
              <p className="text-red-500 text-sm mt-1">{errors.name.message}</p>
            )}
          </div>

          {/* Body Part */}
          <div>
            <label className="text-base font-medium mb-2 block">
              Body Part
            </label>
            <Select onValueChange={(value) => setValue('body_part', value)}>
              <SelectTrigger>
                <SelectValue placeholder="Select body part" />
              </SelectTrigger>
              <SelectContent>
                {bodyParts.map((part) => (
                  <SelectItem key={part.value} value={part.value}>
                    {part.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            {errors.body_part && (
              <p className="text-red-500 text-sm mt-1">{errors.body_part.message}</p>
            )}
          </div>

          {/* Modality */}
          <div>
            <label className="text-base font-medium mb-2 block">
              Modality
            </label>
            <Select onValueChange={(value) => setValue('modality', value as ExerciseModality)}>
              <SelectTrigger>
                <SelectValue placeholder="Select modality" />
              </SelectTrigger>
              <SelectContent>
                {modalities.map((modality) => (
                  <SelectItem key={modality.value} value={modality.value}>
                    {modality.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            {errors.modality && (
              <p className="text-red-500 text-sm mt-1">{errors.modality.message}</p>
            )}
          </div>

          {/* Actions */}
          <div className="flex gap-3 pt-4">
            <button
              type="button"
              onClick={handleClose}
              className="btn-secondary flex-1"
              disabled={isSubmitting}
            >
              Cancel
            </button>
            <button
              type="submit"
              className="btn-primary flex-1"
              disabled={isSubmitting || !watch('name') || !watch('body_part') || !watch('modality')}
            >
              {isSubmitting ? 'Adding...' : 'Add Exercise'}
            </button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  )
}
