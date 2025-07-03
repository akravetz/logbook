"use client"

import { useSearchExercisesApiV1ExercisesGet } from "@/lib/api/generated"

export default function ExercisesPage() {
  const { data: exercisesData, isLoading } = useSearchExercisesApiV1ExercisesGet({
    page: 1,
    size: 20,
  })

  return (
    <div className="min-h-screen bg-gray-50 px-6 py-8">
      <h1 className="text-2xl font-bold mb-6">Exercises</h1>

      {isLoading ? (
        <div className="space-y-3">
          {[1, 2, 3, 4, 5].map((i) => (
            <div key={i} className="bg-white rounded-lg p-4 animate-pulse">
              <div className="h-5 bg-gray-200 rounded w-2/3 mb-2" />
              <div className="h-4 bg-gray-200 rounded w-1/2" />
            </div>
          ))}
        </div>
      ) : (
        <div className="space-y-3">
          {exercisesData?.items?.map((exercise) => (
            <div key={exercise.id} className="bg-white rounded-lg p-4">
              <h3 className="font-semibold text-lg">{exercise.name}</h3>
              <div className="flex items-center gap-3 mt-1">
                <span className="exercise-badge">{exercise.body_part}</span>
                <span className="exercise-badge">{exercise.modality.toLowerCase()}</span>
              </div>
            </div>
          ))}

          {(!exercisesData?.items || exercisesData.items.length === 0) && (
            <div className="text-center py-12 text-gray-500">
              <p>No exercises found</p>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
