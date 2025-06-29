"use client"

import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Dumbbell } from "lucide-react"
import { useState } from "react"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { ApiHealthCheck } from "./api-health-check"
import { useInitiateGoogleOauthApiV1AuthGooglePost } from "@/lib/api/generated"
import { signIn } from "next-auth/react"

const isDevelopmentMode = process.env.NODE_ENV === 'development' && process.env.NEXT_PUBLIC_ENABLE_DEV_AUTH === 'true'

export function LoginScreen() {
  const [isDevLoading, setIsDevLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [devEmail, setDevEmail] = useState("")

  // Use the generated API hook for Google OAuth
  const { mutate: initiateGoogleOAuth, isPending: isGoogleLoading } = useInitiateGoogleOauthApiV1AuthGooglePost({
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

  const handleDevLogin = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!devEmail) return

    setError(null)
    setIsDevLoading(true)

    try {
      // Use NextAuth.js signIn with development credentials provider
      const result = await signIn('dev-login', {
        email: devEmail,
        callbackUrl: '/',
        redirect: false,
      })

      if (result?.error) {
        setError("Development login failed. Please try again.")
        setIsDevLoading(false)
      } else if (result?.url) {
        // Successful login - NextAuth will handle the redirect
        window.location.href = result.url
      }

    } catch (error) {
      console.error("Development login error:", error)
      setError("Development login failed. Please try again.")
      setIsDevLoading(false)
    }
  }

  const handleQuickDevLogin = async (email: string) => {
    setDevEmail(email)
    setError(null)
    setIsDevLoading(true)

    try {
      const result = await signIn('dev-login', {
        email,
        callbackUrl: '/',
        redirect: false,
      })

      if (result?.error) {
        setError("Development login failed. Please try again.")
        setIsDevLoading(false)
      } else if (result?.url) {
        window.location.href = result.url
      }

    } catch (error) {
      console.error("Development login error:", error)
      setError("Development login failed. Please try again.")
      setIsDevLoading(false)
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

            <Button
              onClick={handleGoogleLogin}
              disabled={isGoogleLoading || isDevLoading}
              className="w-full"
              size="lg"
            >
              {isGoogleLoading ? "Signing in..." : "Sign in with Google"}
            </Button>

            {isDevelopmentMode && (
              <>
                <div className="relative">
                  <div className="absolute inset-0 flex items-center">
                    <span className="w-full border-t" />
                  </div>
                  <div className="relative flex justify-center text-xs uppercase">
                    <span className="bg-gray-50 px-2 text-muted-foreground">
                      Development Mode
                    </span>
                  </div>
                </div>

                <Card className="border-dashed border-yellow-500 bg-yellow-50">
                  <CardContent className="pt-6">
                    <div className="space-y-4">
                      <div className="text-sm text-yellow-700 font-medium">
                        🚧 Development Authentication
                      </div>

                      <form onSubmit={handleDevLogin} className="space-y-3">
                        <div>
                          <Label htmlFor="dev-email" className="text-xs">
                            Email Address
                          </Label>
                          <Input
                            id="dev-email"
                            type="email"
                            placeholder="developer@example.com"
                            value={devEmail}
                            onChange={(e) => setDevEmail(e.target.value)}
                            disabled={isGoogleLoading || isDevLoading}
                            className="h-8 text-sm"
                            required
                          />
                        </div>
                        <Button
                          type="submit"
                          disabled={isGoogleLoading || isDevLoading || !devEmail}
                          className="w-full h-8 text-sm"
                          variant="outline"
                        >
                          {isDevLoading ? "Signing in..." : "Dev Login"}
                        </Button>
                      </form>

                      <div className="space-y-2">
                        <div className="text-xs text-yellow-600">Quick Login:</div>
                        <div className="flex gap-2">
                          <Button
                            onClick={() => handleQuickDevLogin("admin@example.com")}
                            disabled={isGoogleLoading || isDevLoading}
                            size="sm"
                            variant="outline"
                            className="h-6 text-xs px-2"
                          >
                            Admin
                          </Button>
                          <Button
                            onClick={() => handleQuickDevLogin("user@example.com")}
                            disabled={isGoogleLoading || isDevLoading}
                            size="sm"
                            variant="outline"
                            className="h-6 text-xs px-2"
                          >
                            User
                          </Button>
                          <Button
                            onClick={() => handleQuickDevLogin("test@example.com")}
                            disabled={isGoogleLoading || isDevLoading}
                            size="sm"
                            variant="outline"
                            className="h-6 text-xs px-2"
                          >
                            Test
                          </Button>
                        </div>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </>
            )}

            <div className="pt-4 border-t">
              <ApiHealthCheck />
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
