/**
 * Cache Tags System
 *
 * Defines semantic relationships between data domains to enable
 * declarative cache invalidation without manual dependency tracking.
 */

import { useQueryClient } from '@tanstack/react-query'

// Define semantic cache tags for different data domains
export const CACHE_TAGS = {
  // Workout-related data
  WORKOUT_DATA: 'workout-data',           // Individual workouts and workout lists
  WORKOUT_STATS: 'workout-stats',         // Workout statistics and analytics

  // Exercise-related data
  EXERCISE_DATA: 'exercise-data',         // Exercise search, creation, system exercises
  EXERCISE_CATEGORIES: 'exercise-categories', // Body parts, modalities

  // User-related data
  USER_DATA: 'user-data',                 // User profile and settings
  USER_STATS: 'user-stats',               // User statistics and progress

  // Session and auth data
  SESSION_DATA: 'session-data',           // Authentication and session info
} as const

export type CacheTag = typeof CACHE_TAGS[keyof typeof CACHE_TAGS]

// Helper functions for tag-based cache invalidation
export const cacheUtils = {
  /**
   * Invalidate all queries with specific tags
   */
  invalidateByTags: (queryClient: ReturnType<typeof useQueryClient>, tags: CacheTag[]) => {
    return Promise.all(
      tags.map(tag =>
        queryClient.invalidateQueries({
          predicate: (query) => {
            const queryTags = query.meta?.tags as CacheTag[] | undefined
            return queryTags?.includes(tag) ?? false
          }
        })
      )
    )
  },

  /**
   * Invalidate workout-related data
   * Use this after any workout mutation (reorder, add/delete sets, finish, etc.)
   */
  invalidateWorkoutData: (queryClient: ReturnType<typeof useQueryClient>) => {
    return cacheUtils.invalidateByTags(queryClient, [
      CACHE_TAGS.WORKOUT_DATA,
      CACHE_TAGS.WORKOUT_STATS
    ])
  },

  /**
   * Invalidate exercise-related data
   * Use this after creating new exercises or modifying exercise categories
   */
  invalidateExerciseData: (queryClient: ReturnType<typeof useQueryClient>) => {
    return cacheUtils.invalidateByTags(queryClient, [
      CACHE_TAGS.EXERCISE_DATA,
      CACHE_TAGS.EXERCISE_CATEGORIES
    ])
  },

  /**
   * Invalidate user-related data
   * Use this after profile updates or when user stats change
   */
  invalidateUserData: (queryClient: ReturnType<typeof useQueryClient>) => {
    return cacheUtils.invalidateByTags(queryClient, [
      CACHE_TAGS.USER_DATA,
      CACHE_TAGS.USER_STATS
    ])
  },

  /**
   * Invalidate session data
   * Use this after login/logout or session changes
   */
  invalidateSessionData: (queryClient: ReturnType<typeof useQueryClient>) => {
    return cacheUtils.invalidateByTags(queryClient, [CACHE_TAGS.SESSION_DATA])
  },

  /**
   * Complete data refresh
   * Use this for major state changes that could affect multiple domains
   */
  invalidateAll: (queryClient: ReturnType<typeof useQueryClient>) => {
    return cacheUtils.invalidateByTags(queryClient, Object.values(CACHE_TAGS))
  }
}

/**
 * Hook for easy access to cache invalidation utilities
 *
 * @example
 * const { invalidateWorkoutData } = useCacheUtils()
 * await invalidateWorkoutData() // Invalidates all workout-related caches
 */
export function useCacheUtils() {
  const queryClient = useQueryClient()

  return {
    invalidateByTags: (tags: CacheTag[]) => cacheUtils.invalidateByTags(queryClient, tags),
    invalidateWorkoutData: () => cacheUtils.invalidateWorkoutData(queryClient),
    invalidateExerciseData: () => cacheUtils.invalidateExerciseData(queryClient),
    invalidateUserData: () => cacheUtils.invalidateUserData(queryClient),
    invalidateSessionData: () => cacheUtils.invalidateSessionData(queryClient),
    invalidateAll: () => cacheUtils.invalidateAll(queryClient)
  }
}
