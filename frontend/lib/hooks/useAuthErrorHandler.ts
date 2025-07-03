import { useEffect } from "react"
import { useSession, signOut } from "next-auth/react"

/**
 * Hook that monitors the session for authentication errors and handles them appropriately.
 * Specifically looks for RefreshTokenError which indicates the refresh token has expired.
 */
export function useAuthErrorHandler() {
  const { data: session } = useSession()

  useEffect(() => {
    if (session?.error === "RefreshTokenError") {
      console.warn("Refresh token has expired, forcing re-authentication")
      // Force sign out to clear invalid tokens
      signOut({ callbackUrl: "/" })
    }
  }, [session?.error])
}
