"use client"

import { AppShell } from "@/components/app-shell"
import { WorkoutInterface } from "@/components/workout-interface"
import { useAuth } from "@/lib/contexts/auth-context"
import { LoginScreen } from "@/components/login-screen"
import { ErrorBoundary } from "@/components/error-boundary"

function WorkoutPage() {
  const { user, isLoading } = useAuth()

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background">
        <div className="flex flex-col items-center gap-4">
          <div className="w-8 h-8 border-2 border-primary border-t-transparent rounded-full animate-spin" />
          <p className="text-sm text-muted-foreground">Loading...</p>
        </div>
      </div>
    )
  }

  if (!user) {
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
