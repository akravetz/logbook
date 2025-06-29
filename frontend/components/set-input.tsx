"use client"

import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { useWorkout } from "@/lib/contexts/workout-context"
import { Minus, Plus, Target } from "lucide-react"
import { useState } from "react"

export function SetInput() {
  const { currentExercise, updateCurrentSet, completeSet } = useWorkout()
  const [showForcedReps, setShowForcedReps] = useState(false)

  if (!currentExercise) return null

  const { currentSet } = currentExercise

  const adjustWeight = (delta: number) => {
    const newWeight = Math.max(0, currentSet.weight + delta)
    updateCurrentSet({ weight: newWeight })
  }

  const adjustCleanReps = (delta: number) => {
    const newReps = Math.max(0, currentSet.clean_reps + delta)
    updateCurrentSet({ clean_reps: newReps })
  }

  const adjustForcedReps = (delta: number) => {
    const newReps = Math.max(0, currentSet.forced_reps + delta)
    updateCurrentSet({ forced_reps: newReps })
  }

  const handleCompleteSet = () => {
    completeSet()
    // Add haptic feedback if available
    if (navigator.vibrate) {
      navigator.vibrate(100)
    }
  }

  const formatSetDisplay = () => {
    if (currentSet.forced_reps > 0) {
      return `${currentSet.weight} × ${currentSet.clean_reps}+${currentSet.forced_reps}`
    }
    return `${currentSet.weight} × ${currentSet.clean_reps}`
  }

  return (
    <Card className="w-full">
      <CardHeader>
        <CardTitle className="text-center">Set {currentExercise.sets.length + 1}</CardTitle>
        <div className="text-center text-sm text-muted-foreground">{formatSetDisplay()}</div>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Weight Input */}
        <div className="space-y-2">
          <Label className="text-center block">Weight (lbs)</Label>
          <div className="flex items-center gap-2">
            <Button variant="outline" size="icon" className="h-12 w-12 bg-transparent" onClick={() => adjustWeight(-5)}>
              <Minus className="h-4 w-4" />
            </Button>
            <Input
              type="number"
              value={currentSet.weight}
              onChange={(e) => updateCurrentSet({ weight: Number(e.target.value) })}
              className="text-center text-xl font-bold h-12"
            />
            <Button variant="outline" size="icon" className="h-12 w-12 bg-transparent" onClick={() => adjustWeight(5)}>
              <Plus className="h-4 w-4" />
            </Button>
          </div>
        </div>

        {/* Clean Reps Input */}
        <div className="space-y-2">
          <Label className="text-center block">Clean Reps</Label>
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="icon"
              className="h-12 w-12 bg-transparent"
              onClick={() => adjustCleanReps(-1)}
            >
              <Minus className="h-4 w-4" />
            </Button>
            <Input
              type="number"
              value={currentSet.clean_reps}
              onChange={(e) => updateCurrentSet({ clean_reps: Number(e.target.value) })}
              className="text-center text-xl font-bold h-12"
            />
            <Button
              variant="outline"
              size="icon"
              className="h-12 w-12 bg-transparent"
              onClick={() => adjustCleanReps(1)}
            >
              <Plus className="h-4 w-4" />
            </Button>
          </div>
        </div>

        {/* Forced Reps Input */}
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <Label>Forced Reps (optional)</Label>
            <Button variant="ghost" size="sm" onClick={() => setShowForcedReps(!showForcedReps)}>
              {showForcedReps ? "Hide" : "Add"}
            </Button>
          </div>
          {showForcedReps && (
            <div className="flex items-center gap-2">
              <Button
                variant="outline"
                size="icon"
                className="h-12 w-12 bg-transparent"
                onClick={() => adjustForcedReps(-1)}
              >
                <Minus className="h-4 w-4" />
              </Button>
              <Input
                type="number"
                value={currentSet.forced_reps}
                onChange={(e) => updateCurrentSet({ forced_reps: Number(e.target.value) })}
                className="text-center text-xl font-bold h-12"
              />
              <Button
                variant="outline"
                size="icon"
                className="h-12 w-12 bg-transparent"
                onClick={() => adjustForcedReps(1)}
              >
                <Plus className="h-4 w-4" />
              </Button>
            </div>
          )}
        </div>

        {/* Complete Set Button */}
        <Button
          onClick={handleCompleteSet}
          className="w-full h-14 text-lg font-semibold"
          size="lg"
          disabled={currentSet.weight === 0 || currentSet.clean_reps === 0}
        >
          <Target className="w-5 h-5 mr-2" />
          Complete Set
        </Button>
      </CardContent>
    </Card>
  )
}
