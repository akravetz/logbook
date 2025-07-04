/**
 * Tagged Query Hooks
 *
 * Wraps generated queries with semantic cache tags for declarative
 * cache invalidation. This keeps the generated code intact while
 * adding our tagging system.
 */

import { useQuery, type UseQueryOptions, type UseQueryResult } from '@tanstack/react-query'
import {
  // Workout queries
  getGetWorkoutApiV1WorkoutsWorkoutIdGetQueryOptions,
  getListWorkoutsApiV1WorkoutsGetQueryOptions,
  type GetWorkoutApiV1WorkoutsWorkoutIdGetQueryResult,
  type ListWorkoutsApiV1WorkoutsGetQueryResult,

  // Exercise queries
  getSearchExercisesApiV1ExercisesGetQueryOptions,
  getGetBodyPartsApiV1ExercisesBodyPartsGetQueryOptions,
  getGetModalitiesApiV1ExercisesModalitiesGetQueryOptions,
  type SearchExercisesApiV1ExercisesGetQueryResult,
  type GetBodyPartsApiV1ExercisesBodyPartsGetQueryResult,
  type GetModalitiesApiV1ExercisesModalitiesGetQueryResult,

  // User queries
  getGetCurrentUserProfileApiV1UsersMeGetQueryOptions,
  getGetUserStatisticsApiV1UsersMeStatsGetQueryOptions,
  type GetCurrentUserProfileApiV1UsersMeGetQueryResult,
  type GetUserStatisticsApiV1UsersMeStatsGetQueryResult,

  // Auth queries
  getGetSessionInfoApiV1AuthMeGetQueryOptions,
  type GetSessionInfoApiV1AuthMeGetQueryResult
} from '@/lib/api/generated'
import type {
  ListWorkoutsApiV1WorkoutsGetParams,
  SearchExercisesApiV1ExercisesGetParams,
  GetUserStatisticsApiV1UsersMeStatsGetParams
} from '@/lib/api/model'
import { CACHE_TAGS, type CacheTag } from '@/lib/cache-tags'

// Utility to add tags to query options
function withTags<T>(
  queryOptions: UseQueryOptions<T>,
  tags: CacheTag[]
): UseQueryOptions<T> {
  return {
    ...queryOptions,
    meta: {
      ...queryOptions.meta,
      tags
    }
  }
}

// ========================================
// WORKOUT QUERIES
// ========================================

/**
 * Get individual workout with workout-data tag
 */
export function useTaggedGetWorkout(
  workoutId: number,
  options?: {
    query?: Partial<UseQueryOptions<GetWorkoutApiV1WorkoutsWorkoutIdGetQueryResult>>
    request?: any
  }
): UseQueryResult<GetWorkoutApiV1WorkoutsWorkoutIdGetQueryResult> {
  const queryOptions = getGetWorkoutApiV1WorkoutsWorkoutIdGetQueryOptions(workoutId, options)

  return useQuery(
    withTags(queryOptions, [CACHE_TAGS.WORKOUT_DATA])
  )
}

/**
 * Get workout list with workout-data tag
 */
export function useTaggedListWorkouts(
  params?: ListWorkoutsApiV1WorkoutsGetParams,
  options?: {
    query?: Partial<UseQueryOptions<ListWorkoutsApiV1WorkoutsGetQueryResult>>
    request?: any
  }
): UseQueryResult<ListWorkoutsApiV1WorkoutsGetQueryResult> {
  const queryOptions = getListWorkoutsApiV1WorkoutsGetQueryOptions(params, options)

  return useQuery(
    withTags(queryOptions, [CACHE_TAGS.WORKOUT_DATA])
  )
}

// ========================================
// EXERCISE QUERIES
// ========================================

/**
 * Search exercises with exercise-data tag
 */
export function useTaggedSearchExercises(
  params?: SearchExercisesApiV1ExercisesGetParams,
  options?: {
    query?: Partial<UseQueryOptions<SearchExercisesApiV1ExercisesGetQueryResult>>
    request?: any
  }
): UseQueryResult<SearchExercisesApiV1ExercisesGetQueryResult> {
  const queryOptions = getSearchExercisesApiV1ExercisesGetQueryOptions(params, options)

  return useQuery(
    withTags(queryOptions, [CACHE_TAGS.EXERCISE_DATA])
  )
}

/**
 * Get body parts with exercise-categories tag
 */
export function useTaggedGetBodyParts(
  options?: {
    query?: Partial<UseQueryOptions<GetBodyPartsApiV1ExercisesBodyPartsGetQueryResult>>
    request?: any
  }
): UseQueryResult<GetBodyPartsApiV1ExercisesBodyPartsGetQueryResult> {
  const queryOptions = getGetBodyPartsApiV1ExercisesBodyPartsGetQueryOptions(options)

  return useQuery(
    withTags(queryOptions, [CACHE_TAGS.EXERCISE_CATEGORIES])
  )
}

/**
 * Get modalities with exercise-categories tag
 */
export function useTaggedGetModalities(
  options?: {
    query?: Partial<UseQueryOptions<GetModalitiesApiV1ExercisesModalitiesGetQueryResult>>
    request?: any
  }
): UseQueryResult<GetModalitiesApiV1ExercisesModalitiesGetQueryResult> {
  const queryOptions = getGetModalitiesApiV1ExercisesModalitiesGetQueryOptions(options)

  return useQuery(
    withTags(queryOptions, [CACHE_TAGS.EXERCISE_CATEGORIES])
  )
}

// ========================================
// USER QUERIES
// ========================================

/**
 * Get current user profile with user-data tag
 */
export function useTaggedGetCurrentUserProfile(
  options?: {
    query?: Partial<UseQueryOptions<GetCurrentUserProfileApiV1UsersMeGetQueryResult>>
    request?: any
  }
): UseQueryResult<GetCurrentUserProfileApiV1UsersMeGetQueryResult> {
  const queryOptions = getGetCurrentUserProfileApiV1UsersMeGetQueryOptions(options)

  return useQuery(
    withTags(queryOptions, [CACHE_TAGS.USER_DATA])
  )
}

/**
 * Get user statistics with user-stats tag
 */
export function useTaggedGetUserStatistics(
  params?: GetUserStatisticsApiV1UsersMeStatsGetParams,
  options?: {
    query?: Partial<UseQueryOptions<GetUserStatisticsApiV1UsersMeStatsGetQueryResult>>
    request?: any
  }
): UseQueryResult<GetUserStatisticsApiV1UsersMeStatsGetQueryResult> {
  const queryOptions = getGetUserStatisticsApiV1UsersMeStatsGetQueryOptions(params, options)

  return useQuery(
    withTags(queryOptions, [CACHE_TAGS.USER_STATS])
  )
}

// ========================================
// SESSION QUERIES
// ========================================

/**
 * Get session info with session-data tag
 */
export function useTaggedGetSessionInfo(
  options?: {
    query?: Partial<UseQueryOptions<GetSessionInfoApiV1AuthMeGetQueryResult>>
    request?: any
  }
): UseQueryResult<GetSessionInfoApiV1AuthMeGetQueryResult> {
  const queryOptions = getGetSessionInfoApiV1AuthMeGetQueryOptions(options)

  return useQuery(
    withTags(queryOptions, [CACHE_TAGS.SESSION_DATA])
  )
}
