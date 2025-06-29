"use client"

import { useAuth } from "@/lib/contexts/auth-context"
import { LoginScreen } from "@/components/login-screen"
import { AppShell } from "@/components/app-shell"
import { DashboardScreen } from "@/components/dashboard-screen"
import { ErrorBoundary } from "@/components/error-boundary"
import { useEffect, useState } from "react"

function HomePage() {
  const { user, isLoading } = useAuth()
  const [mounted, setMounted] = useState(false)

  useEffect(() => {
    setMounted(true)
  }, [])

  if (!mounted || isLoading) {
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
      <DashboardScreen />
    </AppShell>
  )
}

export default function Page() {
  return (
    <ErrorBoundary>
      <HomePage />
    </ErrorBoundary>
  )
}
