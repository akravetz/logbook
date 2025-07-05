"use client"

import { useEffect, useMemo, useState } from 'react'
import { useRouter } from 'next/navigation'
import { useSession } from 'next-auth/react'
import { Check, GripVertical, Mic, Trash2, Plus } from 'lucide-react'
import {
  DndContext,
  closestCenter,
  KeyboardSensor,
  PointerSensor,
  useSensor,
  useSensors,
  DragEndEvent,
} from '@dnd-kit/core'
import {
  arrayMove,
  SortableContext,
  sortableKeyboardCoordinates,
  verticalListSortingStrategy,
  useSortable,
} from '@dnd-kit/sortable'
import { CSS } from '@dnd-kit/utilities'
import { useWorkoutStore } from '@/lib/stores/workout-store'
import { useUIStore } from '@/lib/stores/ui-store'
import {
  useFinishWorkoutApiV1WorkoutsWorkoutIdFinishPatch,
  useUpsertExerciseExecutionApiV1WorkoutsWorkoutIdExerciseExecutionsExerciseIdPut,
  useReorderExercisesApiV1WorkoutsWorkoutIdExerciseExecutionsReorderPatch
} from '@/lib/api/generated'
import { useCacheUtils } from '@/lib/cache-tags'
import type { ExerciseExecutionRequest, SetCreate, ExerciseExecutionResponse } from '@/lib/api/model'

interface ActiveWorkoutScreenProps {
  workoutId: number
}

interface SortableExerciseCardProps {
  execution: ExerciseExecutionResponse
  isWorkoutFinished: boolean
  deletingSetId: number | null
  onDeleteSet: (exerciseId: number, setId: number) => void
  onOpenEditSetModal: (exerciseId: number, setId: number, currentData: any) => void
  onOpenAddSetModal: (exerciseId: number, exerciseData: any) => void
  onOpenVoiceNoteModal: (exerciseId: number, exerciseName: string) => void
}

function SortableExerciseCard({
  execution,
  isWorkoutFinished,
  deletingSetId,
  onDeleteSet,
  onOpenEditSetModal,
  onOpenAddSetModal,
  onOpenVoiceNoteModal,
}: SortableExerciseCardProps) {
  const {
    attributes,
    listeners,
    setNodeRef,
    transform,
    transition,
    isDragging,
  } = useSortable({ id: execution.exercise_id })

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
    opacity: isDragging ? 0.5 : 1,
  }

  return (
    <div
      ref={setNodeRef}
      style={style}
      className={`bg-white rounded-lg shadow-sm ${isDragging ? 'shadow-lg ring-2 ring-blue-200' : ''}`}
    >
      {/* Exercise header */}
      <div className="p-4 border-b border-gray-100">
        <div className="flex items-start justify-between">
          <div className="flex items-start gap-3">
            <button
              {...attributes}
              {...listeners}
              className={`touch-none p-1 rounded hover:bg-gray-100 transition-colors ${
                isWorkoutFinished ? 'cursor-not-allowed opacity-50' : 'cursor-grab active:cursor-grabbing'
              }`}
              disabled={isWorkoutFinished}
              aria-label="Drag to reorder exercise"
            >
              <GripVertical className="w-5 h-5 text-gray-400" />
            </button>
            <div>
              <h3 className="font-semibold text-lg">{execution.exercise_name}</h3>
              <div className="flex items-center gap-3 mt-1">
                <span className="exercise-badge">{execution.exercise_body_part}</span>
                <span className="exercise-badge">{execution.exercise_modality.toLowerCase()}</span>
              </div>
              {execution.note_text && (
                <div className="mt-2 p-3 bg-gray-50 rounded-lg border border-gray-200">
                  <p className="text-sm text-gray-700 font-medium">Note: {execution.note_text}</p>
                </div>
              )}
            </div>
          </div>
          {!isWorkoutFinished && (
            <div className="flex items-center gap-2">
              <button
                className="p-2 hover:bg-gray-100 rounded transition-colors"
                onClick={() => onOpenVoiceNoteModal(execution.exercise_id, execution.exercise_name)}
              >
                <Mic className="w-5 h-5 text-gray-400" />
              </button>
              <button className="p-2">
                <Trash2 className="w-5 h-5 text-gray-400" />
              </button>
            </div>
          )}
        </div>
      </div>

      {/* Sets */}
      <div className="p-4">
        {execution.sets && execution.sets.length > 0 ? (
          <div className="space-y-3">
            {execution.sets.map((set, index) => (
              <div key={set.id} className="flex items-center justify-between">
                <div className="text-gray-600">
                  Set {index + 1}
                </div>
                <div className="flex items-center gap-4">
                  <span className="font-medium">
                    {set.weight} lb × {set.clean_reps} reps
                    {set.forced_reps > 0 && ` + ${set.forced_reps}`}
                  </span>
                  {!isWorkoutFinished && (
                    <>
                      <button
                        onClick={() => onOpenEditSetModal(execution.exercise_id, set.id, set)}
                        className="text-blue-600 font-medium"
                        disabled={deletingSetId === set.id}
                      >
                        Edit
                      </button>
                      <button
                        onClick={() => onDeleteSet(execution.exercise_id, set.id)}
                        disabled={deletingSetId === set.id}
                        className="p-1 disabled:opacity-50 disabled:cursor-not-allowed hover:bg-red-50 rounded transition-colors"
                      >
                        <Trash2 className={`w-4 h-4 ${deletingSetId === set.id ? 'text-red-400 animate-pulse' : 'text-gray-400 hover:text-red-600'}`} />
                      </button>
                    </>
                  )}
                </div>
              </div>
            ))}
          </div>
        ) : null}

        {!isWorkoutFinished && (
          <button
            onClick={() => onOpenAddSetModal(execution.exercise_id, {
              id: execution.exercise_id,
              name: execution.exercise_name,
              body_part: execution.exercise_body_part,
              modality: execution.exercise_modality,
            })}
            className="w-full mt-4 py-3 border border-gray-300 rounded-lg font-medium flex items-center justify-center gap-2 active:scale-[0.98] transition-transform"
          >
            <Plus className="w-4 h-4" />
            Add Set
          </button>
        )}
      </div>
    </div>
  )
}

export function ActiveWorkoutScreen({ workoutId }: ActiveWorkoutScreenProps) {
  const router = useRouter()
  const { data: session } = useSession()
  const { invalidateWorkoutData } = useCacheUtils()
  const {
    activeWorkout,
    workoutTimer,
    stopTimer,
    resetTimer,
    setActiveWorkout,
    updateExerciseInWorkout,
    reorderExercises,
  } = useWorkoutStore()

  const { openSelectExerciseModal, openAddSetModal, openEditSetModal, openVoiceNoteModal } = useUIStore()

  const [deletingSetId, setDeletingSetId] = useState<number | null>(null)
  const [isReordering, setIsReordering] = useState(false)

  const finishWorkoutMutation = useFinishWorkoutApiV1WorkoutsWorkoutIdFinishPatch()
  const upsertExecutionMutation = useUpsertExerciseExecutionApiV1WorkoutsWorkoutIdExerciseExecutionsExerciseIdPut()
  const reorderExercisesMutation = useReorderExercisesApiV1WorkoutsWorkoutIdExerciseExecutionsReorderPatch()

  // Configure drag and drop sensors
  const sensors = useSensors(
    useSensor(PointerSensor, {
      activationConstraint: {
        distance: 8,
      },
    }),
    useSensor(KeyboardSensor, {
      coordinateGetter: sortableKeyboardCoordinates,
    })
  )

  // Format timer display
  const formattedTime = useMemo(() => {
    const minutes = Math.floor(workoutTimer / 60)
    const seconds = workoutTimer % 60
    return `${minutes}:${seconds.toString().padStart(2, '0')}`
  }, [workoutTimer])

  const handleFinishWorkout = async () => {
    if (!activeWorkout?.id) return

    try {
      const result = await finishWorkoutMutation.mutateAsync({ workoutId: activeWorkout.id })

      // Invalidate workout data using cache tags
      await invalidateWorkoutData()

      stopTimer()
      resetTimer()
      setActiveWorkout(null)

      // Show appropriate feedback based on whether workout was deleted or finished
      if (result.deleted) {
        // Empty workout was deleted - user feedback could be added here
        console.log('Empty workout deleted')
      } else {
        // Workout was finished normally - user feedback could be added here
        console.log('Workout completed!')
      }

      router.push('/')
    } catch (error) {
      // Log error for debugging in development
      if (process.env.NODE_ENV === 'development') {
        console.error('Failed to finish workout:', error)
      }
    }
  }

  const handleDeleteSet = async (exerciseId: number, setId: number) => {
    if (!activeWorkout?.id || deletingSetId) return

    setDeletingSetId(setId)

    try {
      // Find the current exercise execution
      const currentExecution = activeWorkout.exercise_executions?.find(
        (ex) => ex.exercise_id === exerciseId
      )

      if (!currentExecution) return

      // Remove the target set and convert remaining sets to SetCreate format
      const updatedSets: SetCreate[] = (currentExecution.sets || [])
        .filter((set) => set.id !== setId)
        .map((set) => ({
          weight: set.weight,
          clean_reps: set.clean_reps,
          forced_reps: set.forced_reps,
          note_text: set.note_text,
        }))

      // Prepare the exercise execution update
      const executionData: ExerciseExecutionRequest = {
        sets: updatedSets,
        exercise_order: currentExecution.exercise_order,
        note_text: currentExecution.note_text,
      }

      // Call the upsert API
      const updatedExecution = await upsertExecutionMutation.mutateAsync({
        workoutId: activeWorkout.id,
        exerciseId,
        data: executionData,
      })

      // Invalidate workout data using cache tags
      await invalidateWorkoutData()

      // Update local state
      updateExerciseInWorkout(updatedExecution)
    } catch (error) {
      // Log error for debugging in development
      if (process.env.NODE_ENV === 'development') {
        console.error('Failed to delete set:', error)
      }
    } finally {
      setDeletingSetId(null)
    }
  }

  const handleDragEnd = async (event: DragEndEvent) => {
    const { active, over } = event

    if (!over || !activeWorkout?.exercise_executions || isReordering) {
      return
    }

    const activeId = active.id as number
    const overId = over.id as number

    if (activeId !== overId) {
      const oldExercises = activeWorkout.exercise_executions
      const oldIndex = oldExercises.findIndex((ex) => ex.exercise_id === activeId)
      const newIndex = oldExercises.findIndex((ex) => ex.exercise_id === overId)

      if (oldIndex === -1 || newIndex === -1) return

      // Create new ordered array
      const newExercises = arrayMove(oldExercises, oldIndex, newIndex)

      // Optimistically update local state
      reorderExercises(newExercises)
      setIsReordering(true)

      try {
        // Call the reorder API with exercise IDs in new order
        const exerciseIds = newExercises.map((ex) => ex.exercise_id)

        const result = await reorderExercisesMutation.mutateAsync({
          workoutId: activeWorkout.id,
          data: { exercise_ids: exerciseIds }
        })

        // Invalidate workout data using cache tags
        await invalidateWorkoutData()

        // Update state with the API response
        reorderExercises(result.exercise_executions)
      } catch (error) {
        // Rollback on error
        reorderExercises(oldExercises)

        // Log error for debugging in development
        if (process.env.NODE_ENV === 'development') {
          console.error('Failed to reorder exercises:', error)
        }
      } finally {
        setIsReordering(false)
      }
    }
  }

  const getFirstName = () => {
    if (!session?.user?.name) return "User"
    return session.user.name.split(" ")[0]
  }

  // Check if workout is finished
  const isWorkoutFinished = !!activeWorkout?.finished_at

  // Get exercise IDs for sortable context
  const exerciseIds = activeWorkout?.exercise_executions?.map((ex) => ex.exercise_id) || []

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white px-6 py-4 border-b border-gray-100">
        <div className="flex items-center justify-between mb-2">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-gray-200 rounded-full flex items-center justify-center">
              <span className="text-sm font-semibold text-gray-600">
                {session?.user?.name?.[0]?.toUpperCase() || 'U'}
              </span>
            </div>
            <h1 className="text-xl font-semibold">{getFirstName()}</h1>
          </div>

          {!isWorkoutFinished && (
            <button
              onClick={handleFinishWorkout}
              disabled={finishWorkoutMutation.isPending}
              className="bg-black text-white px-4 py-2 rounded-lg font-medium flex items-center gap-2 active:scale-[0.98] transition-transform"
            >
              <Check className="w-4 h-4" />
              {finishWorkoutMutation.isPending ? 'Finishing...' : 'Finish'}
            </button>
          )}
        </div>

        <div>
          <h2 className="text-2xl font-bold">Active Workout</h2>
          <p className="text-gray-600">
            {formattedTime}
            {isReordering && ' • Reordering...'}
          </p>
        </div>
      </div>

      {/* Exercises */}
      <div className="px-6 py-4">
        {activeWorkout?.exercise_executions && activeWorkout.exercise_executions.length > 0 ? (
          <DndContext
            sensors={sensors}
            collisionDetection={closestCenter}
            onDragEnd={handleDragEnd}
          >
            <SortableContext items={exerciseIds} strategy={verticalListSortingStrategy}>
              <div className="space-y-4">
                {activeWorkout.exercise_executions.map((execution) => (
                  <SortableExerciseCard
                    key={execution.exercise_id}
                    execution={execution}
                    isWorkoutFinished={isWorkoutFinished}
                    deletingSetId={deletingSetId}
                    onDeleteSet={handleDeleteSet}
                    onOpenEditSetModal={openEditSetModal}
                    onOpenAddSetModal={openAddSetModal}
                    onOpenVoiceNoteModal={openVoiceNoteModal}
                  />
                ))}
              </div>
            </SortableContext>
          </DndContext>
        ) : null}

        {/* Add Exercise button */}
        {!isWorkoutFinished && (
          <button
            onClick={openSelectExerciseModal}
            className="w-full mt-4 py-4 border border-gray-300 rounded-lg font-medium flex items-center justify-center gap-2 active:scale-[0.98] transition-transform"
          >
            <Plus className="w-5 h-5" />
            Add Exercise
          </button>
        )}
      </div>
    </div>
  )
}
