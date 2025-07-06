/**
 * Utilities for optimistic updates
 */

/**
 * Generates a temporary ID for optimistic updates
 */
export function generateOptimisticId(): string {
  return `temp-${Date.now()}-${Math.random().toString(36).substring(2, 9)}`
}

/**
 * Checks if an ID is optimistic (temporary)
 */
export function isOptimisticId(id: string | number): boolean {
  return typeof id === 'string' && id.startsWith('temp-')
}

/**
 * Type guard for optimistic data
 */
export function isOptimisticData<T extends { id: string | number }>(data: T): data is T & { isOptimistic: true } {
  return isOptimisticId(data.id)
}

/**
 * Creates optimistic exercise execution data
 */
export function createOptimisticExerciseExecution(
  exercise: { id: number; name: string; body_part: string; modality: string },
  exerciseOrder: number
): OptimisticExerciseExecution {
  return {
    id: generateOptimisticId(),
    exercise_id: exercise.id,
    exercise_name: exercise.name,
    exercise_body_part: exercise.body_part,
    exercise_modality: exercise.modality,
    exercise_order: exerciseOrder,
    sets: [],
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
    isOptimistic: true
  }
}

/**
 * Creates optimistic set data
 */
export function createOptimisticSet(
  setData: { weight: number; clean_reps: number; forced_reps: number; note_text?: string },
  id?: string
): OptimisticSet {
  return {
    id: id || generateOptimisticId(),
    weight: setData.weight,
    clean_reps: setData.clean_reps,
    forced_reps: setData.forced_reps,
    note_text: setData.note_text || '',
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
    isOptimistic: true
  }
}

/**
 * Extended exercise execution type with optimistic flag
 */
export interface OptimisticExerciseExecution {
  id: string // Optimistic ID
  exercise_id: number
  exercise_name: string
  exercise_body_part: string
  exercise_modality: string
  exercise_order: number
  sets: any[]
  created_at: string
  updated_at: string
  isOptimistic: true
}

/**
 * Extended set type with optimistic flag
 */
export interface OptimisticSet {
  id: string // Optimistic ID
  weight: number
  clean_reps: number
  forced_reps: number
  note_text: string
  created_at: string
  updated_at: string
  isOptimistic: true
}

/**
 * Operation queue for handling dependent operations
 */
export interface PendingOperation {
  id: string
  type: 'ADD_SET' | 'UPDATE_SET' | 'DELETE_SET' | 'ADD_EXERCISE_NOTE' | 'OPTIMISTIC_MUTATION'
  dependsOn?: string // ID of operation this depends on
  data: any
  execute: () => Promise<void>
  rollback: () => void
}

/**
 * Creates a pending operation
 */
export function createPendingOperation(
  type: PendingOperation['type'],
  data: any,
  execute: () => Promise<void>,
  rollback: () => void,
  dependsOn?: string
): PendingOperation {
  return {
    id: generateOptimisticId(),
    type,
    data,
    execute,
    rollback,
    dependsOn
  }
}
