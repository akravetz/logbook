"use client"

import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { useWorkout } from "@/lib/contexts/workout-context"
import { Timer, Plus, CheckCircle } from "lucide-react"
import { SetInput } from "./set-input"
import { ExerciseSelector } from "./exercise-selector"
import { useState } from "react"

export function WorkoutInterface() {
  const { currentExercise, workoutTimer, isWorkoutActive, finishWorkout } = useWorkout()

  const [showExerciseSelector, setShowExerciseSelector] = useState(!currentExercise)

  const formatTime = (seconds: number) => {
    const hours = Math.floor(seconds / 3600)
    const minutes = Math.floor((seconds % 3600) / 60)
    const secs = seconds % 60

    if (hours > 0) {
      return `${hours}:${minutes.toString().padStart(2, "0")}:${secs.toString().padStart(2, "0")}`
    }
    return `${minutes}:${secs.toString().padStart(2, "0")}`
  }

  const handleFinishWorkout = () => {
    finishWorkout()
  }

  if (!isWorkoutActive) {
    return (
      <div className="p-4 text-center">
        <h2 className="text-xl font-bold mb-4">No active workout</h2>
        <p className="text-muted-foreground">Start a workout from the dashboard</p>
      </div>
    )
  }

  if (showExerciseSelector) {
    return <ExerciseSelector />
  }

  return (
    <div className="p-4 space-y-6">
      {/* Workout Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Timer className="h-5 w-5 text-primary" />
          <span className="text-xl font-bold">{formatTime(workoutTimer)}</span>
        </div>
        <Button onClick={handleFinishWorkout} variant="outline">
          Finish
        </Button>
      </div>

      {/* Current Exercise */}
      {currentExercise && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">💪 {currentExercise.exercise_name}</CardTitle>
            <div className="text-sm text-muted-foreground">Last: 185×8+2, 185×6 {/* This would come from API */}</div>
          </CardHeader>
          <CardContent className="space-y-4">
            {/* Completed Sets */}
            {currentExercise.sets.map((set, index) => (
              <div key={index} className="flex items-center justify-between p-3 bg-muted/50 rounded-lg">
                <span className="font-medium">Set {index + 1}:</span>
                <div className="flex items-center gap-2">
                  <span>
                    {set.weight} × {set.clean_reps}
                    {set.forced_reps > 0 && `+${set.forced_reps}`}
                  </span>
                  <CheckCircle className="h-4 w-4 text-green-500" />
                </div>
              </div>
            ))}

            {/* Current Set Indicator */}
            <div className="flex items-center justify-between p-3 border-2 border-primary rounded-lg">
              <span className="font-medium">Set {currentExercise.sets.length + 1}:</span>
              <span className="text-muted-foreground">In progress...</span>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Set Input */}
      <SetInput />

      {/* Add Exercise Button */}
      <Button onClick={() => setShowExerciseSelector(true)} variant="outline" className="w-full h-12">
        <Plus className="h-4 w-4 mr-2" />
        Add Exercise
      </Button>
    </div>
  )
}
