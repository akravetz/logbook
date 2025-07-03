"use client"

import { useRouter } from 'next/navigation'
import { useSession } from 'next-auth/react'
import { Plus } from 'lucide-react'
import { format } from 'date-fns'
import { useListWorkoutsApiV1WorkoutsGet, useCreateWorkoutApiV1WorkoutsPost } from '@/lib/api/generated'
import { useWorkoutStore } from '@/lib/stores/workout-store'

export function WorkoutsListScreen() {
  const router = useRouter()
  const { data: session } = useSession()
  const { setActiveWorkout, startTimer } = useWorkoutStore()

  // Fetch workouts
  const { data: workoutsData, isLoading } = useListWorkoutsApiV1WorkoutsGet({
    page: 1,
    size: 20,
  })

  // Create workout mutation
  const createWorkoutMutation = useCreateWorkoutApiV1WorkoutsPost()

  const handleNewWorkout = async () => {
    try {
      const result = await createWorkoutMutation.mutateAsync()
      setActiveWorkout(result)
      startTimer()
      router.push('/workout')
    } catch (error) {
      console.error('Failed to create workout:', error)
    }
  }

  const getFirstName = () => {
    if (!session?.user?.name) return "there"
    return session.user.name.split(" ")[0]
  }

  const formatDuration = (minutes: number) => {
    if (minutes < 60) return `${minutes}m`
    const hours = Math.floor(minutes / 60)
    const mins = minutes % 60
    return mins > 0 ? `${hours}h ${mins}m` : `${hours}h`
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white px-6 py-8 border-b border-gray-100">
        <div className="flex items-center gap-4 mb-1">
          <div className="w-12 h-12 bg-gray-200 rounded-full flex items-center justify-center">
            <span className="text-lg font-semibold text-gray-600">
              {session?.user?.name?.[0]?.toUpperCase() || 'U'}
            </span>
          </div>
          <h1 className="text-2xl font-bold">{getFirstName()}</h1>
        </div>
      </div>

      {/* Workouts list */}
      <div className="px-6 py-4">
        <h2 className="text-xl font-semibold mb-4">Workouts</h2>

        {/* New Workout Button */}
        <button
          onClick={handleNewWorkout}
          disabled={createWorkoutMutation.isPending}
          className="w-full bg-black text-white rounded-lg p-4 flex items-center justify-center gap-3 mb-4 font-medium active:scale-[0.98] transition-transform"
        >
          <Plus className="w-5 h-5" />
          {createWorkoutMutation.isPending ? 'Creating...' : 'New Workout'}
        </button>

        {/* Workouts */}
        {isLoading ? (
          <div className="space-y-3">
            {[1, 2, 3].map((i) => (
              <div key={i} className="bg-white rounded-lg p-4 animate-pulse">
                <div className="h-5 bg-gray-200 rounded w-1/3 mb-3" />
                <div className="h-4 bg-gray-200 rounded w-1/2 mb-2" />
                <div className="space-y-2">
                  <div className="h-3 bg-gray-200 rounded w-3/4" />
                  <div className="h-3 bg-gray-200 rounded w-2/3" />
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="space-y-3">
            {workoutsData?.items?.map((workout) => (
              <button
                key={workout.id}
                onClick={() => router.push(`/workout/${workout.id}`)}
                className="w-full bg-white rounded-lg p-4 text-left active:scale-[0.98] transition-transform"
              >
                <div className="flex items-center justify-between mb-2">
                  <h3 className="font-semibold text-lg">
                    {format(new Date(workout.created_at), 'EEEE')} Workout
                  </h3>
                  <span className="text-sm text-gray-500">
                    {workout.exercise_executions?.length || 0} exercises
                  </span>
                </div>

                <div className="flex items-center gap-4 text-sm text-gray-600 mb-3">
                  <span>{format(new Date(workout.created_at), 'MMM d, yyyy')}</span>
                  {workout.finished_at && (
                    <>
                      <span>•</span>
                      <span>{formatDuration(
                        Math.round(
                          (new Date(workout.finished_at).getTime() - new Date(workout.created_at).getTime()) / 60000
                        )
                      )}</span>
                    </>
                  )}
                </div>

                {workout.exercise_executions && workout.exercise_executions.length > 0 && (
                  <div className="space-y-1">
                    {workout.exercise_executions.slice(0, 3).map((execution) => (
                      <div key={execution.exercise_id} className="flex items-center justify-between text-sm">
                        <span className="text-gray-700">{execution.exercise_name}</span>
                        <span className="text-gray-500">{execution.sets?.length || 0} sets</span>
                      </div>
                    ))}
                    {workout.exercise_executions.length > 3 && (
                      <div className="text-sm text-gray-500">
                        +{workout.exercise_executions.length - 3} more exercises
                      </div>
                    )}
                  </div>
                )}
              </button>
            ))}

            {(!workoutsData?.items || workoutsData.items.length === 0) && (
              <div className="text-center py-12 text-gray-500">
                <p className="mb-2">No workouts yet</p>
                <p className="text-sm">Tap "New Workout" to get started!</p>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}
