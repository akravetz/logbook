import { useQuery } from '@tanstack/react-query'
import { useSession } from 'next-auth/react'
import { searchExercisesApiV1ExercisesGet } from '@/lib/api/generated'
import type { ExerciseResponse } from '@/lib/api/model'
import { CACHE_TAGS } from '@/lib/cache-tags'

/**
 * Hook to fetch and cache all exercises for fuzzy searching
 * This replaces multiple API calls with a single cached dataset
 */
export function useExerciseDataCache() {
  const { data: session } = useSession()
  const userId = session?.userId

  return useQuery({
    queryKey: [CACHE_TAGS.EXERCISE_DATA, 'all-exercises', userId],
    queryFn: async () => {
      // Fetch all exercises in batches to avoid pagination limits
      const allExercises: ExerciseResponse[] = []
      let currentPage = 1
      const pageSize = 100 // Maximum allowed by backend

      while (true) {
        const response = await searchExercisesApiV1ExercisesGet({
          page: currentPage,
          size: pageSize,
        })

        if (response.items && response.items.length > 0) {
          allExercises.push(...response.items)
        }

        // Check if we've reached the last page
        if (response.items.length < pageSize || currentPage >= response.pages) {
          break
        }

        currentPage++
      }

      return allExercises
    },
    staleTime: 5 * 60 * 1000, // 5 minutes - exercises don't change frequently
    gcTime: 10 * 60 * 1000, // 10 minutes - keep in cache longer
    refetchOnWindowFocus: false, // Don't refetch on window focus
    refetchOnMount: false, // Don't refetch on mount if data exists
    retry: 2, // Retry failed requests
  })
}

/**
 * Hook to get the current user ID for permission filtering
 */
export function useCurrentUserId(): number | null {
  const { data: session } = useSession()
  return session?.userId ? Number(session.userId) : null
}
