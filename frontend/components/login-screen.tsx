"use client"

import { useState } from "react"
import { signIn } from "next-auth/react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { ApiHealthCheck } from "./api-health-check"

export function LoginScreen() {
  const [isLoading, setIsLoading] = useState(false)
  const [isDevLoading, setIsDevLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [devEmail, setDevEmail] = useState("")

  const isDevelopment = process.env.NODE_ENV === "development"

  const handleGoogleLogin = async () => {
    setError(null)
    setIsLoading(true)

    try {
      // Use NextAuth.js signIn with Google provider
      const result = await signIn('google', {
        callbackUrl: '/', // Redirect to home after successful login
        redirect: false, // Handle the redirect manually to show errors
      })

      if (result?.error) {
        setError("Authentication failed. Please try again.")
        setIsLoading(false)
      } else if (result?.url) {
        // Successful login - NextAuth will handle the redirect
        window.location.href = result.url
      }

    } catch (error) {
      console.error("Unexpected error:", error)
      setError("An unexpected error occurred. Please try again.")
      setIsLoading(false)
    }
  }

  const handleDevLogin = async (e: React.FormEvent) => {
    e.preventDefault()

    if (!devEmail.trim()) {
      setError("Please enter an email address")
      return
    }

    setError(null)
    setIsDevLoading(true)

    try {
      // Use NextAuth.js signIn with dev-login provider
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
      console.error("Unexpected error during dev login:", error)
      setError("An unexpected error occurred during dev login.")
      setIsDevLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8">
        <Card>
          <CardHeader className="text-center">
            <CardTitle className="text-3xl font-bold">LogBK</CardTitle>
            <CardDescription>
              Your personal workout tracking companion
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            {error && (
              <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
                {error}
              </div>
            )}

            <Button
              onClick={handleGoogleLogin}
              disabled={isLoading}
              className="w-full"
              size="lg"
            >
              {isLoading ? "Signing in..." : "Sign in with Google"}
            </Button>

            {isDevelopment && (
              <div className="pt-4 border-t">
                <div className="text-center text-sm text-gray-600 mb-4">
                  Development Mode
                </div>
                <form onSubmit={handleDevLogin}>
                  <div className="space-y-4">
                    <div>
                      <Label htmlFor="dev-email">Development Email</Label>
                      <Input
                        id="dev-email"
                        type="email"
                        placeholder="developer@example.com"
                        value={devEmail}
                        onChange={(e) => setDevEmail(e.target.value)}
                        required
                      />
                    </div>
                    <Button
                      type="submit"
                      disabled={isDevLoading || isLoading}
                      className="w-full"
                      variant="outline"
                      size="lg"
                    >
                      {isDevLoading ? "Logging in..." : "Dev Login"}
                    </Button>
                  </div>
                </form>
              </div>
            )}

            <div className="pt-4 border-t">
              <ApiHealthCheck />
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
