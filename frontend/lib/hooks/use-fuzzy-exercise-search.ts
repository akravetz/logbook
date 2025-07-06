import { useMemo } from 'react'
import { useDebounce } from '@/lib/hooks/use-debounce'
import { useExerciseDataCache, useCurrentUserId } from '@/lib/search/exercise-data-cache'
import { FuzzySearchService } from '@/lib/search/fuzzy-search-service'
import type {
  SearchExercisesApiV1ExercisesGetParams,
  PageExerciseResponse
} from '@/lib/api/model'

// Create a singleton instance of the fuzzy search service
let fuzzySearchService: FuzzySearchService | null = null

function getFuzzySearchService(): FuzzySearchService {
  if (!fuzzySearchService) {
    fuzzySearchService = new FuzzySearchService()
  }
  return fuzzySearchService
}

export interface UseFuzzyExerciseSearchOptions {
  query?: {
    enabled?: boolean
    staleTime?: number
    gcTime?: number
  }
  request?: any
}

export interface UseFuzzyExerciseSearchResult {
  data: PageExerciseResponse | undefined
  isLoading: boolean
  error: Error | null
  refetch: () => void
}

/**
 * Hook for fuzzy exercise search that replaces API calls with local search
 * Maintains the same interface as the original useTaggedSearchExercises hook
 */
export function useFuzzyExerciseSearch(
  params?: SearchExercisesApiV1ExercisesGetParams,
  options?: UseFuzzyExerciseSearchOptions
): UseFuzzyExerciseSearchResult {
  const userId = useCurrentUserId()
  const enabled = options?.query?.enabled ?? true

  // Debounce the search term to avoid excessive calculations
  const debouncedSearchTerm = useDebounce(params?.name || '', 300)

  // Fetch the exercise data cache
  const {
    data: exerciseData,
    isLoading: isLoadingData,
    error: cacheError,
    refetch
  } = useExerciseDataCache()

  // Perform the fuzzy search using memoization for performance
  const searchResults = useMemo(() => {
    if (!enabled || !exerciseData || isLoadingData) {
      return undefined
    }

    const service = getFuzzySearchService()

    // Update the service with the latest exercise data
    service.setExercises(exerciseData)

    // Create search parameters
    const filters = {
      name: debouncedSearchTerm || null,
      body_part: params?.body_part || null,
      modality: params?.modality || null,
      is_user_created: params?.is_user_created ?? null,
      created_by_user_id: params?.created_by_user_id || null,
    }

    const pagination = {
      page: params?.page || 1,
      size: params?.size || 20,
      offset: ((params?.page || 1) - 1) * (params?.size || 20),
    }

    // Perform the search
    const result = service.search(filters, pagination, userId)

    // Convert to the expected PageExerciseResponse format
    const pageResponse: PageExerciseResponse = {
      items: result.items,
      total: result.total,
      page: result.page,
      size: result.size,
      pages: result.pages,
    }

    return pageResponse
  }, [
    enabled,
    exerciseData,
    isLoadingData,
    debouncedSearchTerm,
    params?.body_part,
    params?.modality,
    params?.is_user_created,
    params?.created_by_user_id,
    params?.page,
    params?.size,
    userId,
  ])

  return {
    data: searchResults,
    isLoading: isLoadingData,
    error: cacheError,
    refetch,
  }
}

/**
 * Hook for getting exercises by body part with fuzzy search
 */
export function useFuzzyExercisesByBodyPart(
  bodyPart: string,
  params?: { page?: number; size?: number },
  options?: UseFuzzyExerciseSearchOptions
): UseFuzzyExerciseSearchResult {
  return useFuzzyExerciseSearch({
    body_part: bodyPart,
    page: params?.page,
    size: params?.size,
  }, options)
}

/**
 * Hook for getting exercises by modality with fuzzy search
 */
export function useFuzzyExercisesByModality(
  modality: string,
  params?: { page?: number; size?: number },
  options?: UseFuzzyExerciseSearchOptions
): UseFuzzyExerciseSearchResult {
  return useFuzzyExerciseSearch({
    modality,
    page: params?.page,
    size: params?.size,
  }, options)
}

/**
 * Hook for getting user's own exercises with fuzzy search
 */
export function useFuzzyUserExercises(
  params?: { page?: number; size?: number },
  options?: UseFuzzyExerciseSearchOptions
): UseFuzzyExerciseSearchResult {
  const userId = useCurrentUserId()

  return useFuzzyExerciseSearch({
    created_by_user_id: userId || undefined,
    is_user_created: true,
    page: params?.page,
    size: params?.size,
  }, options)
}

/**
 * Hook for getting system exercises with fuzzy search
 */
export function useFuzzySystemExercises(
  params?: { page?: number; size?: number },
  options?: UseFuzzyExerciseSearchOptions
): UseFuzzyExerciseSearchResult {
  return useFuzzyExerciseSearch({
    is_user_created: false,
    page: params?.page,
    size: params?.size,
  }, options)
}
