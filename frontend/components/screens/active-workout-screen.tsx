"use client"

import { useEffect, useMemo } from 'react'
import { useRouter } from 'next/navigation'
import { useSession } from 'next-auth/react'
import { Check, GripVertical, Mic, Trash2, Plus } from 'lucide-react'
import { useWorkoutStore } from '@/lib/stores/workout-store'
import { useUIStore } from '@/lib/stores/ui-store'
import { useFinishWorkoutApiV1WorkoutsWorkoutIdFinishPatch } from '@/lib/api/generated'

interface ActiveWorkoutScreenProps {
  workoutId?: number
}

export function ActiveWorkoutScreen({ workoutId }: ActiveWorkoutScreenProps) {
  const router = useRouter()
  const { data: session } = useSession()
  const {
    activeWorkout,
    workoutTimer,
    stopTimer,
    resetTimer,
  } = useWorkoutStore()

  const { openAddExerciseModal, openAddSetModal, openEditSetModal } = useUIStore()

  const finishWorkoutMutation = useFinishWorkoutApiV1WorkoutsWorkoutIdFinishPatch()

  // Format timer display
  const formattedTime = useMemo(() => {
    const minutes = Math.floor(workoutTimer / 60)
    const seconds = workoutTimer % 60
    return `${minutes}:${seconds.toString().padStart(2, '0')}`
  }, [workoutTimer])

  const handleFinishWorkout = async () => {
    if (!activeWorkout?.id) return

    try {
      await finishWorkoutMutation.mutateAsync({ workoutId: activeWorkout.id })
      stopTimer()
      resetTimer()
      router.push('/')
    } catch (error) {
      // Log error for debugging in development
      if (process.env.NODE_ENV === 'development') {
        console.error('Failed to finish workout:', error)
      }
    }
  }

  const getFirstName = () => {
    if (!session?.user?.name) return "User"
    return session.user.name.split(" ")[0]
  }

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

          <button
            onClick={handleFinishWorkout}
            disabled={finishWorkoutMutation.isPending}
            className="bg-black text-white px-4 py-2 rounded-lg font-medium flex items-center gap-2 active:scale-[0.98] transition-transform"
          >
            <Check className="w-4 h-4" />
            {finishWorkoutMutation.isPending ? 'Finishing...' : 'Finish'}
          </button>
        </div>

        <div>
          <h2 className="text-2xl font-bold">Active Workout</h2>
          <p className="text-gray-600">{formattedTime}</p>
        </div>
      </div>

      {/* Exercises */}
      <div className="px-6 py-4">
        {activeWorkout?.exercise_executions && activeWorkout.exercise_executions.length > 0 ? (
          <div className="space-y-4">
            {activeWorkout.exercise_executions.map((execution) => (
              <div key={execution.exercise_id} className="bg-white rounded-lg shadow-sm">
                {/* Exercise header */}
                <div className="p-4 border-b border-gray-100">
                  <div className="flex items-start justify-between">
                    <div className="flex items-start gap-3">
                      <GripVertical className="w-5 h-5 text-gray-400 mt-0.5" />
                      <div>
                        <h3 className="font-semibold text-lg">{execution.exercise_name}</h3>
                        <div className="flex items-center gap-3 mt-1">
                          <span className="exercise-badge">chest</span>
                          <span className="exercise-badge">barbell</span>
                        </div>
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      <button className="p-2">
                        <Mic className="w-5 h-5 text-gray-400" />
                      </button>
                      <button className="p-2">
                        <Trash2 className="w-5 h-5 text-gray-400" />
                      </button>
                    </div>
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
                            <button
                              onClick={() => openEditSetModal(execution.exercise_id, set.id, set)}
                              className="text-blue-600 font-medium"
                            >
                              Edit
                            </button>
                            <button className="p-1">
                              <Trash2 className="w-4 h-4 text-gray-400" />
                            </button>
                          </div>
                        </div>
                      ))}
                    </div>
                  ) : null}

                  <button
                    onClick={() => openAddSetModal(execution.exercise_id, {
                      id: execution.exercise_id,
                      name: execution.exercise_name,
                      body_part: 'chest', // TODO: Get from actual exercise data
                      modality: 'barbell', // TODO: Get from actual exercise data
                    })}
                    className="w-full mt-4 py-3 border border-gray-300 rounded-lg font-medium flex items-center justify-center gap-2 active:scale-[0.98] transition-transform"
                  >
                    <Plus className="w-4 h-4" />
                    Add Set
                  </button>
                </div>
              </div>
            ))}
          </div>
        ) : null}

        {/* Add Exercise button */}
        <button
          onClick={openAddExerciseModal}
          className="w-full mt-4 py-4 border border-gray-300 rounded-lg font-medium flex items-center justify-center gap-2 active:scale-[0.98] transition-transform"
        >
          <Plus className="w-5 h-5" />
          Add Exercise
        </button>
      </div>
    </div>
  )
}
