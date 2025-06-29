"use client"

import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { useState } from "react"
import { useSimpleHealthCheckApiV1HealthGet } from "@/lib/api/generated"

export function ApiHealthCheck() {
  const [manualCheck, setManualCheck] = useState(false)
  const [result, setResult] = useState<string | null>(null)

  // Use the generated API hook for automatic health checking
  const {
    data: healthData,
    error: healthError,
    isLoading: isAutoChecking,
    refetch: refetchHealth,
  } = useSimpleHealthCheckApiV1HealthGet({
    query: {
      enabled: false, // Don't auto-fetch, only on manual trigger
    },
  })

  const checkApiHealth = async () => {
    setManualCheck(true)
    setResult(null)

    try {
      const result = await refetchHealth()

      if (result.data) {
        setResult(`✅ API is healthy: ${JSON.stringify(result.data)}`)
      } else if (result.error) {
        setResult(`❌ API error: ${result.error instanceof Error ? result.error.message : "Unknown error"}`)
      }
    } catch (error) {
      console.error("Health check failed:", error)
      setResult(`❌ Failed to connect: ${error instanceof Error ? error.message : "Unknown error"}`)
    } finally {
      setManualCheck(false)
    }
  }

  if (process.env.NODE_ENV !== "development") {
    return null
  }

  const isChecking = isAutoChecking || manualCheck
  const errorMessage = healthError instanceof Error ? healthError.message : healthError ? String(healthError) : null

  return (
    <Card className="w-full max-w-md mt-4">
      <CardHeader>
        <CardTitle className="text-sm">API Health Check (Dev Only)</CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        <Button
          onClick={checkApiHealth}
          disabled={isChecking}
          variant="outline"
          size="sm"
          className="w-full bg-transparent"
        >
          {isChecking ? "Checking..." : "Test API Connection"}
        </Button>
        {result && <div className="text-xs p-2 bg-muted rounded">{result}</div>}
        {errorMessage && (
          <div className="text-xs p-2 bg-red-100 text-red-800 rounded">
            ❌ Health check error: {errorMessage}
          </div>
        )}
      </CardContent>
    </Card>
  )
}
