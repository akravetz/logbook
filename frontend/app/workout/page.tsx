"use client"

import { AppShell } from "@/components/app-shell"
import { WorkoutInterface } from "@/components/workout-interface"
import { useSession } from "next-auth/react"
import { LoginScreen } from "@/components/login-screen"
import { ErrorBoundary } from "@/components/error-boundary"

function WorkoutPage() {
  const { data: session, status } = useSession()

  if (status === "loading") {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background">
        <div className="flex flex-col items-center gap-4">
          <div className="w-8 h-8 border-2 border-primary border-t-transparent rounded-full animate-spin" />
          <p className="text-sm text-muted-foreground">Loading...</p>
        </div>
      </div>
    )
  }

  if (status === "unauthenticated" || !session) {
    return <LoginScreen />
  }

  return (
    <AppShell>
      <WorkoutInterface />
    </AppShell>
  )
}

export default function Page() {
  return (
    <ErrorBoundary>
      <WorkoutPage />
    </ErrorBoundary>
  )
}
