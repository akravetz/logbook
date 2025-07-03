"use client"

import { useEffect } from "react"
import { useSession } from "next-auth/react"
import { useRouter } from "next/navigation"
import { LoginScreen } from "@/components/screens/login-screen"
import { ActiveWorkoutScreen } from "@/components/screens/active-workout-screen"
import { AddExerciseModal } from "@/components/modals/add-exercise-modal"
import { AddSetModal } from "@/components/modals/add-set-modal"
import { EditSetModal } from "@/components/modals/edit-set-modal"
import { useWorkoutStore } from "@/lib/stores/workout-store"
import { useGetWorkoutApiV1WorkoutsWorkoutIdGet } from "@/lib/api/generated"

export default function WorkoutPage() {
  const { data: session, status } = useSession()
  const router = useRouter()
  const { activeWorkout, setActiveWorkout, startTimer } = useWorkoutStore()

  // If there's no active workout, redirect to home
  useEffect(() => {
    if (status === "authenticated" && !activeWorkout) {
      router.push("/")
    }
  }, [status, activeWorkout, router])

  if (status === "loading") {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="flex flex-col items-center gap-4">
          <div className="w-8 h-8 border-2 border-black border-t-transparent rounded-full animate-spin" />
          <p className="text-sm text-gray-600">Loading...</p>
        </div>
      </div>
    )
  }

  if (status === "unauthenticated" || !session) {
    return <LoginScreen />
  }

  if (!activeWorkout) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center">
          <p className="text-gray-600 mb-4">No active workout</p>
          <button
            onClick={() => router.push("/")}
            className="btn-primary"
          >
            Start New Workout
          </button>
        </div>
      </div>
    )
  }

  return (
    <>
      <ActiveWorkoutScreen />
      <AddExerciseModal />
      <AddSetModal />
      <EditSetModal />
    </>
  )
}
