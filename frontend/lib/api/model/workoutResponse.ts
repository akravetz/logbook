/**
 * Generated by orval v6.31.0 🍺
 * Do not edit manually.
 * Workout API
 * A workout tracking API built with FastAPI
 * OpenAPI spec version: 1.0.0
 */
import type { ExerciseExecutionResponse } from "./exerciseExecutionResponse";
import type { WorkoutResponseFinishedAt } from "./workoutResponseFinishedAt";

/**
 * Schema for workout responses.
 */
export interface WorkoutResponse {
  created_at: string;
  created_by_user_id: number;
  exercise_executions?: ExerciseExecutionResponse[];
  finished_at?: WorkoutResponseFinishedAt;
  id: number;
  updated_at: string;
  updated_by_user_id: number;
}
