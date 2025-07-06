"use client"

import { useState, useMemo } from 'react'
import { Search, Plus } from 'lucide-react'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/modal'
import { useUIStore } from '@/lib/stores/ui-store'
import { useWorkoutStore } from '@/lib/stores/workout-store'
import {
  useUpsertExerciseExecutionApiV1WorkoutsWorkoutIdExerciseExecutionsExerciseIdPut
} from '@/lib/api/generated'
import { useTaggedSearchExercises } from '@/lib/hooks/use-tagged-queries'
import { useCacheUtils } from '@/lib/cache-tags'
import type { ExerciseExecutionRequest, ExerciseResponse } from '@/lib/api/model'
import { useDebounce } from '@/lib/hooks/use-debounce'
import { logger } from '@/lib/logger'

export function SelectExerciseModal() {
  const { modals, closeAllModals, openAddNewExerciseModal } = useUIStore()
  const { activeWorkout, addExerciseToWorkout } = useWorkoutStore()
  const { invalidateWorkoutData } = useCacheUtils()
  const [searchTerm, setSearchTerm] = useState('')
  const [isAdding, setIsAdding] = useState<number | null>(null)

  const debouncedSearchTerm = useDebounce(searchTerm, 300)

  const { data: searchResults, isLoading } = useTaggedSearchExercises({
    name: debouncedSearchTerm || undefined,
    page: 1,
    size: 50,
  }, {
    query: {
      enabled: true, // Always fetch exercises, search term is optional
    }
  })

  const upsertExecutionMutation = useUpsertExerciseExecutionApiV1WorkoutsWorkoutIdExerciseExecutionsExerciseIdPut()

  // Group exercises by body part
  const groupedExercises = useMemo(() => {
    if (!searchResults?.items) return {}

    return searchResults.items.reduce((groups: Record<string, ExerciseResponse[]>, exercise: ExerciseResponse) => {
      const bodyPart = exercise.body_part
      if (!groups[bodyPart]) {
        groups[bodyPart] = []
      }
      groups[bodyPart].push(exercise)
      return groups
    }, {} as Record<string, ExerciseResponse[]>)
  }, [searchResults?.items])

  const handleSelectExercise = async (exercise: ExerciseResponse) => {
    if (!activeWorkout?.id || isAdding === exercise.id) return

    setIsAdding(exercise.id)

    try {
      const executionData: ExerciseExecutionRequest = {
        sets: [],
        exercise_order: (activeWorkout.exercise_executions?.length || 0) + 1,
      }

      const executionResult = await upsertExecutionMutation.mutateAsync({
        workoutId: activeWorkout.id,
        exerciseId: exercise.id,
        data: executionData,
      })

      // Invalidate workout data using cache tags
      await invalidateWorkoutData()

      // Update local state
      addExerciseToWorkout(executionResult)

      // Close modal
      closeAllModals()
    } catch (error) {
      // Log error for debugging
      logger.error('Failed to add exercise to workout:', error)
    } finally {
      setIsAdding(null)
    }
  }

  const handleClose = () => {
    setSearchTerm('')
    closeAllModals()
  }

  const getModalityDisplayName = (modality: string) => {
    const modalityMap: Record<string, string> = {
      'DUMBBELL': 'dumbbell',
      'BARBELL': 'barbell',
      'CABLE': 'cable',
      'MACHINE': 'machine',
      'SMITH': 'smith',
      'BODYWEIGHT': 'bodyweight',
    }
    return modalityMap[modality] || modality.toLowerCase()
  }

  const capitalizeBodyPart = (bodyPart: string) => {
    return bodyPart.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())
  }

  return (
    <Dialog open={modals.selectExercise} onOpenChange={handleClose}>
      <DialogContent className="max-w-md max-h-[80vh] flex flex-col">
        <DialogHeader>
          <DialogTitle>Select Exercise</DialogTitle>
        </DialogHeader>

        {/* Search Bar */}
        <div className="relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
          <input
            type="text"
            placeholder="Search exercises..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pl-10 pr-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-black focus:border-transparent"
            autoFocus
          />
        </div>

        {/* Add New Exercise Button */}
        <button
          onClick={openAddNewExerciseModal}
          className="w-full py-3 border border-gray-300 rounded-lg font-medium flex items-center justify-center gap-2 hover:bg-gray-50 transition-colors"
        >
          <Plus className="w-4 h-4" />
          Add New Exercise
        </button>

        {/* Exercise List */}
        <div className="flex-1 overflow-y-auto space-y-4">
          {isLoading ? (
            <div className="space-y-3">
              {[1, 2, 3, 4, 5].map((i) => (
                <div key={i} className="animate-pulse">
                  <div className="h-4 bg-gray-200 rounded w-20 mb-2" />
                  <div className="space-y-2">
                    <div className="h-12 bg-gray-100 rounded-lg" />
                    <div className="h-12 bg-gray-100 rounded-lg" />
                  </div>
                </div>
              ))}
            </div>
          ) : Object.keys(groupedExercises).length > 0 ? (
            Object.entries(groupedExercises).map(([bodyPart, exercises]) => (
              <div key={bodyPart}>
                <h3 className="font-semibold text-gray-900 mb-2">
                  {capitalizeBodyPart(bodyPart)}
                </h3>
                <div className="space-y-2">
                  {exercises.map((exercise) => (
                    <button
                      key={exercise.id}
                      onClick={() => handleSelectExercise(exercise)}
                      disabled={isAdding === exercise.id}
                      className="w-full p-3 text-left border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      <div className="flex items-center justify-between">
                        <div className="flex-1">
                          <div className="font-medium text-gray-900">
                            {exercise.name}
                          </div>
                        </div>
                        <div className="ml-3">
                          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-800">
                            {getModalityDisplayName(exercise.modality)}
                          </span>
                        </div>
                      </div>
                    </button>
                  ))}
                </div>
              </div>
            ))
          ) : searchTerm ? (
                         <div className="text-center py-8 text-gray-500">
               <p>No exercises found for &quot;{searchTerm}&quot;</p>
               <p className="text-sm mt-1">Try a different search term</p>
             </div>
          ) : (
            <div className="text-center py-8 text-gray-500">
              <p>No exercises available</p>
            </div>
          )}
        </div>
      </DialogContent>
    </Dialog>
  )
}
