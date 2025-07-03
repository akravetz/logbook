"use client"

import { useState } from "react"
import { signIn } from "next-auth/react"

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
      const result = await signIn('google', {
        callbackUrl: '/',
        redirect: false,
      })

      if (result?.error) {
        setError("Authentication failed. Please try again.")
        setIsLoading(false)
      } else if (result?.url) {
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
      const result = await signIn('dev-login', {
        email: devEmail,
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
      console.error("Unexpected error during dev login:", error)
      setError("An unexpected error occurred during dev login.")
      setIsDevLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex flex-col items-center justify-center px-6 bg-gray-50">
      <div className="w-full max-w-sm">
        {/* Logo/Title */}
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold mb-2">LogBK</h1>
          <p className="text-gray-600">Your workout companion</p>
        </div>

        {/* Error message */}
        {error && (
          <div className="mb-6 p-4 bg-red-50 border border-red-200 text-red-700 rounded-lg text-sm">
            {error}
          </div>
        )}

        {/* Login buttons */}
        <div className="space-y-4">
          <button
            onClick={handleGoogleLogin}
            disabled={isLoading || isDevLoading}
            className="btn-primary w-full"
          >
            {isLoading ? "Signing in..." : "Sign in with Google"}
          </button>

          {isDevelopment && (
            <>
              <div className="relative">
                <div className="absolute inset-0 flex items-center">
                  <div className="w-full border-t border-gray-300" />
                </div>
                <div className="relative flex justify-center text-sm">
                  <span className="px-2 bg-gray-50 text-gray-500">Development Mode</span>
                </div>
              </div>

              <form onSubmit={handleDevLogin} className="space-y-4">
                <input
                  type="email"
                  placeholder="developer@example.com"
                  value={devEmail}
                  onChange={(e) => setDevEmail(e.target.value)}
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-black focus:border-transparent"
                  required
                />
                <button
                  type="submit"
                  disabled={isDevLoading || isLoading}
                  className="btn-secondary w-full"
                >
                  {isDevLoading ? "Logging in..." : "Dev Login"}
                </button>
              </form>
            </>
          )}
        </div>
      </div>
    </div>
  )
}
