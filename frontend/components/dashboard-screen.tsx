"use client"

import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { useAuth } from "@/lib/contexts/auth-context"
import { useWorkout } from "@/lib/contexts/workout-context"
import { Flame, Dumbbell, TrendingUp, ArrowRight } from "lucide-react"
import { useRouter } from "next/navigation"
import { useEffect, useState } from "react"

export function DashboardScreen() {
  const { user } = useAuth()
  const { startWorkout } = useWorkout()
  const router = useRouter()
  const [mounted, setMounted] = useState(false)

  useEffect(() => {
    setMounted(true)
  }, [])

  const handleStartWorkout = () => {
    startWorkout()
    router.push("/workout")
  }

  const getGreeting = () => {
    if (!mounted) return "Hello"
    const hour = new Date().getHours()
    if (hour < 12) return "Good morning"
    if (hour < 17) return "Good afternoon"
    return "Good evening"
  }

  const getFirstName = () => {
    if (!user?.name) return "there"
    return user.name.split(" ")[0]
  }

  if (!mounted) {
    return (
      <div className="p-4 space-y-6">
        <div className="h-8 bg-muted animate-pulse rounded" />
        <div className="grid grid-cols-2 gap-4">
          <div className="h-20 bg-muted animate-pulse rounded" />
          <div className="h-20 bg-muted animate-pulse rounded" />
        </div>
        <div className="h-16 bg-muted animate-pulse rounded" />
      </div>
    )
  }

  return (
    <div className="p-4 space-y-6">
      {/* Greeting */}
      <div className="space-y-1">
        <h1 className="text-2xl font-bold">
          {getGreeting()}, {getFirstName()}!
        </h1>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-2 gap-4">
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-2">
              <Flame className="w-5 h-5 text-orange-500" />
              <div>
                <div className="text-2xl font-bold">3</div>
                <div className="text-sm text-muted-foreground">day streak</div>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-2">
              <Dumbbell className="w-5 h-5 text-blue-500" />
              <div>
                <div className="text-2xl font-bold">12</div>
                <div className="text-sm text-muted-foreground">workouts this month</div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Start Workout CTA */}
      <Button onClick={handleStartWorkout} className="w-full h-16 text-lg font-semibold" size="lg">
        <TrendingUp className="w-6 h-6 mr-2" />
        Start New Workout
      </Button>

      {/* Recent Activity */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">Recent Activity</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <div className="flex items-center justify-between py-2">
            <div>
              <div className="font-medium">Mon: Push (45 min)</div>
              <div className="text-sm text-muted-foreground">6 exercises • 18 sets</div>
            </div>
            <div className="text-green-500">✅</div>
          </div>
          <div className="flex items-center justify-between py-2">
            <div>
              <div className="font-medium">Fri: Pull (52 min)</div>
              <div className="text-sm text-muted-foreground">5 exercises • 15 sets</div>
            </div>
            <div className="text-green-500">✅</div>
          </div>
          <div className="flex items-center justify-between py-2">
            <div>
              <div className="font-medium">Wed: Legs (38 min)</div>
              <div className="text-sm text-muted-foreground">4 exercises • 12 sets</div>
            </div>
            <div className="text-green-500">✅</div>
          </div>
          <Button variant="ghost" className="w-full mt-4">
            View All History
            <ArrowRight className="w-4 h-4 ml-2" />
          </Button>
        </CardContent>
      </Card>
    </div>
  )
}
