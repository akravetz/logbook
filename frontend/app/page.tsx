"use client"

import { useSession } from "next-auth/react"
import { LoginScreen } from "@/components/login-screen"
import { DashboardScreen } from "@/components/dashboard-screen"
import { ErrorBoundary } from "@/components/error-boundary"

export default function HomePage() {
  const { data: session, status } = useSession()

  if (status === "loading") {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-lg">Loading...</div>
      </div>
    )
  }

  if (!session) {
    return <LoginScreen />
  }

  return <DashboardScreen />
}
