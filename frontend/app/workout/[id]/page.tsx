"use client"

import { useEffect, useState } from "react"
import { useSession } from "next-auth/react"
import { useRouter } from "next/navigation"
import { LoginScreen } from "@/components/screens/login-screen"
import { ActiveWorkoutScreen } from "@/components/screens/active-workout-screen"
import { SelectExerciseModal } from "@/components/modals/select-exercise-modal"
import { AddExerciseModal } from "@/components/modals/add-exercise-modal"
import { AddSetModal } from "@/components/modals/add-set-modal"
import { EditSetModal } from "@/components/modals/edit-set-modal"
import { VoiceNoteModal } from "@/components/modals/voice-note-modal"
import { useWorkoutStore } from "@/lib/stores/workout-store"
import { useTaggedGetWorkout } from "@/lib/hooks/use-tagged-queries"

interface WorkoutPageProps {
  params: Promise<{ id: string }>
}

export default function WorkoutPage({ params }: WorkoutPageProps) {
  const { data: session, status } = useSession()
  const router = useRouter()
  const { activeWorkout, setActiveWorkout, startTimer } = useWorkoutStore()

  const [workoutId, setWorkoutId] = useState<number | null>(null)

  // Extract the workoutId from params
  useEffect(() => {
    params.then((resolvedParams) => {
      setWorkoutId(parseInt(resolvedParams.id))
    })
  }, [params])

  // Fetch the workout data with cache tags
  const { data: workoutData, isLoading, error } = useTaggedGetWorkout(
    workoutId || 0,
    {
      query: {
        enabled: !!workoutId && status === "authenticated",
      }
    }
  )

  // Set the active workout when data loads
  useEffect(() => {
    if (workoutData) {
      setActiveWorkout(workoutData)

      // Start timer if workout is not finished
      if (!workoutData.finished_at) {
        startTimer()
      }
    }
  }, [workoutData, setActiveWorkout, startTimer])

  // Redirect to home if workout not found or user not authenticated
  useEffect(() => {
    if (status === "authenticated" && error) {
      router.push("/")
    }
  }, [status, error, router])

  if (status === "loading" || isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="flex flex-col items-center gap-4">
          <div className="w-8 h-8 border-2 border-black border-t-transparent rounded-full animate-spin" />
          <p className="text-sm text-gray-600">Loading workout...</p>
        </div>
      </div>
    )
  }

  if (status === "unauthenticated" || !session) {
    return <LoginScreen />
  }

  if (error || !workoutData) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center">
          <p className="text-gray-600 mb-4">Workout not found</p>
          <button
            onClick={() => router.push("/")}
            className="btn-primary"
          >
            Back to Home
          </button>
        </div>
      </div>
    )
  }

  // Check if workout is finished
  if (workoutData.finished_at) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center">
          <p className="text-gray-600 mb-4">This workout has been completed</p>
          <p className="text-sm text-gray-500 mb-4">
            Finished on {new Date(workoutData.finished_at).toLocaleDateString()}
          </p>
          <button
            onClick={() => router.push("/")}
            className="btn-primary"
          >
            Back to Home
          </button>
        </div>
      </div>
    )
  }

  return (
    <>
      <ActiveWorkoutScreen workoutId={workoutId || 0} />
      <SelectExerciseModal />
      <AddExerciseModal />
      <AddSetModal />
      <EditSetModal />
      <VoiceNoteModal />
    </>
  )
}
