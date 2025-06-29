"use client"

import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Badge } from "@/components/ui/badge"
import { Search, Plus } from "lucide-react"
import { useState } from "react"
import { useWorkout } from "@/lib/contexts/workout-context"

// Mock data - in real app this would come from your generated API client
const mockExercises = [
  { id: 1, name: "Bench Press", body_part: "Chest", modality: "BARBELL", lastWeight: 185, lastReps: "8+2" },
  { id: 2, name: "Squat", body_part: "Legs", modality: "BARBELL", lastWeight: 225, lastReps: "10" },
  { id: 3, name: "Deadlift", body_part: "Back", modality: "BARBELL", lastWeight: 275, lastReps: "6" },
  { id: 4, name: "Incline Press", body_part: "Chest", modality: "DUMBBELL", lastWeight: 70, lastReps: "10" },
  { id: 5, name: "Pull-ups", body_part: "Back", modality: "BODYWEIGHT", lastWeight: 25, lastReps: "8+1" },
]

const bodyParts = ["Chest", "Back", "Legs", "Shoulders", "Arms"]

export function ExerciseSelector() {
  const [searchTerm, setSearchTerm] = useState("")
  const [selectedBodyPart, setSelectedBodyPart] = useState<string | null>(null)
  const { addExercise } = useWorkout()

  const filteredExercises = mockExercises.filter((exercise) => {
    const matchesSearch = exercise.name.toLowerCase().includes(searchTerm.toLowerCase())
    const matchesBodyPart = !selectedBodyPart || exercise.body_part === selectedBodyPart
    return matchesSearch && matchesBodyPart
  })

  const recentExercises = mockExercises.slice(0, 3)

  const handleAddExercise = (exercise: any) => {
    addExercise(exercise)
  }

  return (
    <div className="p-4 space-y-6">
      {/* Search */}
      <div className="relative">
        <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-muted-foreground h-4 w-4" />
        <Input
          placeholder="Search exercises..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          className="pl-10 h-12"
        />
      </div>

      {/* Recent Exercises */}
      {!searchTerm && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">📝 Recent Exercises</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            {recentExercises.map((exercise) => (
              <div
                key={exercise.id}
                className="flex items-center justify-between p-3 rounded-lg border hover:bg-muted/50 transition-colors"
              >
                <div>
                  <div className="font-medium">{exercise.name}</div>
                  <div className="text-sm text-muted-foreground">
                    Last: {exercise.lastWeight}×{exercise.lastReps}
                  </div>
                </div>
                <Button size="sm" onClick={() => handleAddExercise(exercise)}>
                  <Plus className="h-4 w-4" />
                </Button>
              </div>
            ))}
          </CardContent>
        </Card>
      )}

      {/* Body Part Filters */}
      <div className="space-y-3">
        <h3 className="font-medium">🏷️ Browse by Category</h3>
        <div className="flex flex-wrap gap-2">
          <Badge
            variant={selectedBodyPart === null ? "default" : "outline"}
            className="cursor-pointer"
            onClick={() => setSelectedBodyPart(null)}
          >
            All
          </Badge>
          {bodyParts.map((bodyPart) => (
            <Badge
              key={bodyPart}
              variant={selectedBodyPart === bodyPart ? "default" : "outline"}
              className="cursor-pointer"
              onClick={() => setSelectedBodyPart(bodyPart)}
            >
              {bodyPart}
            </Badge>
          ))}
        </div>
      </div>

      {/* Exercise List */}
      <div className="space-y-2">
        {filteredExercises.map((exercise) => (
          <Card key={exercise.id} className="cursor-pointer hover:bg-muted/50 transition-colors">
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div className="flex-1">
                  <div className="flex items-center gap-2">
                    <span className="font-medium">{exercise.name}</span>
                    <span className="text-lg">
                      {exercise.body_part === "Chest" && "🏋️‍♂️"}
                      {exercise.body_part === "Back" && "📈"}
                      {exercise.body_part === "Legs" && "🦵"}
                      {exercise.body_part === "Shoulders" && "💪"}
                      {exercise.body_part === "Arms" && "💪"}
                    </span>
                  </div>
                  <div className="text-sm text-muted-foreground">
                    {exercise.modality} • Last: {exercise.lastWeight}×{exercise.lastReps}
                  </div>
                </div>
                <Button size="sm" onClick={() => handleAddExercise(exercise)}>
                  <Plus className="h-4 w-4" />
                </Button>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  )
}
