/**
 * Generated by orval v6.31.0 🍺
 * Do not edit manually.
 * Workout API
 * A workout tracking API built with FastAPI
 * OpenAPI spec version: 1.0.0
 */

/**
 * Personal record for an exercise.
 */
export interface PersonalRecord {
  /** Date the PR was achieved */
  achieved_date: string;
  /** Exercise unique identifier */
  exercise_id: number;
  /** Exercise name */
  exercise_name: string;
  /** Maximum volume in a single set */
  max_volume_single_set: number;
  /** Maximum weight lifted */
  max_weight: number;
}
