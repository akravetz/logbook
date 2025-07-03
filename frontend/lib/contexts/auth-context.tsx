"use client"

import { SessionProvider } from "next-auth/react"
import { ReactNode } from "react"
import { useAuthErrorHandler } from "@/lib/hooks/useAuthErrorHandler"

interface AuthProviderProps {
  children: ReactNode
}

// Component that uses the auth error handler hook
function AuthErrorHandler({ children }: { children: ReactNode }) {
  useAuthErrorHandler()
  return <>{children}</>
}

export function AuthProvider({ children }: AuthProviderProps) {
  return (
    <SessionProvider>
      <AuthErrorHandler>{children}</AuthErrorHandler>
    </SessionProvider>
  )
}

// Export useAuth hook that wraps NextAuth's useSession
export { useSession as useAuth } from "next-auth/react"
