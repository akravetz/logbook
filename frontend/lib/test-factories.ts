import type {
  WorkoutResponse,
  ExerciseExecutionResponse,
  SetResponse,
  ExerciseModality
} from '@/lib/api/model'

export const createMockSet = (overrides: Partial<SetResponse> = {}): SetResponse => ({
  id: 1,
  exercise_id: 1,
  weight: 135,
  clean_reps: 8,
  forced_reps: 0,
  note_text: null,
  created_at: new Date().toISOString(),
  updated_at: new Date().toISOString(),
  ...overrides,
})

export const createMockExerciseExecution = (
  overrides: Partial<ExerciseExecutionResponse> = {}
): ExerciseExecutionResponse => ({
  exercise_id: 1,
  exercise_name: 'Bench Press',
  exercise_body_part: 'Chest',
  exercise_modality: 'BARBELL' as ExerciseModality,
  sets: [],
  note_text: null,
  exercise_order: 1,
  created_at: new Date().toISOString(),
  updated_at: new Date().toISOString(),
  ...overrides,
})

export const createMockWorkout = (
  overrides: Partial<WorkoutResponse> = {}
): WorkoutResponse => ({
  id: 1,
  created_by_user_id: 1,
  updated_by_user_id: 1,
  finished_at: null,
  exercise_executions: [],
  created_at: new Date().toISOString(),
  updated_at: new Date().toISOString(),
  ...overrides,
})

// Common workout scenarios
export const createActiveWorkoutWithExercises = (
  exerciseCount: number = 2
): WorkoutResponse => {
  const exercises = Array.from({ length: exerciseCount }, (_, index) =>
    createMockExerciseExecution({
      exercise_id: index + 1,
      exercise_name: `Exercise ${index + 1}`,
      exercise_body_part: index % 2 === 0 ? 'Chest' : 'Back',
      exercise_modality: index % 2 === 0 ? 'BARBELL' : 'DUMBBELL',
      exercise_order: index + 1,
      sets: [
        createMockSet({ id: index * 10 + 1, exercise_id: index + 1, weight: 135 + index * 10 }),
        createMockSet({ id: index * 10 + 2, exercise_id: index + 1, weight: 145 + index * 10 }),
      ],
    })
  )

  return createMockWorkout({
    exercise_executions: exercises,
  })
}

export const createFinishedWorkout = (): WorkoutResponse =>
  createMockWorkout({
    finished_at: new Date().toISOString(),
    exercise_executions: [
      createMockExerciseExecution({
        sets: [createMockSet({ exercise_id: 1 })],
      }),
    ],
  })

export const createEmptyWorkout = (): WorkoutResponse =>
  createMockWorkout({
    exercise_executions: [],
  })
