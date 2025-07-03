"use client"

import { useSession } from "next-auth/react"
import { LoginScreen } from "@/components/screens/login-screen"
import { WorkoutsListScreen } from "@/components/screens/workouts-list-screen"

export default function HomePage() {
  const { data: session, status } = useSession()

  if (status === "loading") {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-lg">Loading...</div>
      </div>
    )
  }

  if (!session) {
    return <LoginScreen />
  }

  return <WorkoutsListScreen />
}
