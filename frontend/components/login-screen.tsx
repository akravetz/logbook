"use client"

import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Dumbbell } from "lucide-react"
import { useState } from "react"
import { ApiHealthCheck } from "./api-health-check"
import { useInitiateGoogleOauthApiV1AuthGooglePost } from "@/lib/api/generated"

export function LoginScreen() {
  const [error, setError] = useState<string | null>(null)

  // Use the generated API hook for Google OAuth
  const { mutate: initiateGoogleOAuth, isPending: isLoading } = useInitiateGoogleOauthApiV1AuthGooglePost({
    mutation: {
      onSuccess: (data) => {
        console.log("Auth response:", data)
        if (data.authorization_url) {
          window.location.href = data.authorization_url
        } else {
          setError("No authorization URL received")
        }
      },
      onError: (error) => {
        console.error("Login failed:", error)

        // Set user-friendly error message
        if (error instanceof TypeError && error.message === "Failed to fetch") {
          setError(
            "Unable to connect to authentication service. This might be due to CORS policy or network issues. Please check the browser console for more details.",
          )
        } else if (error instanceof Error) {
          setError(error.message)
        } else {
          setError("An unexpected error occurred. Please try again.")
        }
      },
    },
  })

  const handleGoogleLogin = async () => {
    setError(null)

    try {
      // Call the generated API client
      initiateGoogleOAuth({
        params: {
          // Add redirect_url if needed
          redirect_url: undefined,
        },
      })
    } catch (error) {
      console.error("Unexpected error:", error)
      setError("An unexpected error occurred. Please try again.")
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-background p-4">
      <div className="w-full max-w-md space-y-4">
        <Card>
          <CardHeader className="text-center space-y-4">
            <div className="flex justify-center">
              <div className="flex items-center justify-center w-16 h-16 rounded-full bg-primary">
                <Dumbbell className="w-8 h-8 text-primary-foreground" />
              </div>
            </div>
            <div>
              <CardTitle className="text-2xl font-bold">getswole.ai</CardTitle>
              <CardDescription className="text-lg">AI-Powered Gains</CardDescription>
            </div>
          </CardHeader>
          <CardContent className="space-y-6">
            {error && (
              <div className="p-3 text-sm text-red-600 bg-red-50 border border-red-200 rounded-md dark:bg-red-900/20 dark:border-red-800 dark:text-red-400">
                {error}
              </div>
            )}

            <Button onClick={handleGoogleLogin} disabled={isLoading} className="w-full h-12 text-base" size="lg">
              {isLoading ? (
                <div className="flex items-center gap-2">
                  <div className="w-4 h-4 border-2 border-current border-t-transparent rounded-full animate-spin" />
                  Signing in...
                </div>
              ) : (
                <>Sign in with Google</>
              )}
            </Button>

            <div className="text-center text-sm text-muted-foreground">
              AI-powered workout tracking
              <br />
              for serious lifters
            </div>

            {/* Debug info in development */}
            {process.env.NODE_ENV === "development" && (
              <div className="text-center text-xs text-muted-foreground bg-muted/50 p-2 rounded">
                API URL: {process.env.NEXT_PUBLIC_API_URL || "https://api.getswole.ai"}
              </div>
            )}
          </CardContent>
        </Card>

        <ApiHealthCheck />
      </div>
    </div>
  )
}
