import Fuse, { type IFuseOptions } from 'fuse.js'
import type {
  ExerciseResponse,
  ExerciseModality,
  SearchExercisesApiV1ExercisesGetParams,
  PageExerciseResponse
} from '@/lib/api/model'

export interface ExerciseFilters {
  name?: string | null
  body_part?: string | null
  modality?: string | null
  is_user_created?: boolean | null
  created_by_user_id?: number | null
}

export interface Pagination {
  page: number
  size: number
  offset: number
}

export interface SearchResult {
  items: ExerciseResponse[]
  total: number
  page: number
  size: number
  pages: number
}

export class FuzzySearchService {
  private fuse: Fuse<ExerciseResponse> | null = null
  private exercises: ExerciseResponse[] = []

  constructor() {
    this.initializeFuse()
  }

  private initializeFuse() {
    const options: IFuseOptions<ExerciseResponse> = {
      keys: ['name'],
      threshold: 0.3, // Equivalent to backend's 70% score cutoff (lower = more strict)
      distance: 100,
      minMatchCharLength: 1,
      includeScore: true,
      includeMatches: true,
    }

    this.fuse = new Fuse([], options)
  }

  /**
   * Update the exercise dataset for searching
   */
  setExercises(exercises: ExerciseResponse[]) {
    this.exercises = exercises
    if (this.fuse) {
      this.fuse.setCollection(exercises)
    }
  }

  /**
   * Main search method that replicates backend logic
   */
  search(
    filters: ExerciseFilters,
    pagination: Pagination,
    userId?: number | null
  ): SearchResult {
    // Step 1: Apply permission filtering (same as backend)
    let filteredExercises = this.applyPermissionFilter(this.exercises, userId)

    // Step 2: Apply non-name filters first (same as backend)
    filteredExercises = this.applyNonNameFilters(filteredExercises, filters)

    // Step 3: Apply name filtering with different strategies based on query length
    const nameFilteredExercises = this.applyNameFilter(filteredExercises, filters.name)

    // Step 4: Apply pagination
    const total = nameFilteredExercises.length
    const pages = Math.ceil(total / pagination.size)
    const start = pagination.offset
    const end = start + pagination.size
    const paginatedExercises = nameFilteredExercises.slice(start, end)

    return {
      items: paginatedExercises,
      total,
      page: pagination.page,
      size: pagination.size,
      pages,
    }
  }

  /**
   * Apply permission filtering (user can see their own exercises + system exercises)
   */
  private applyPermissionFilter(
    exercises: ExerciseResponse[],
    userId?: number | null
  ): ExerciseResponse[] {
    if (userId === null || userId === undefined) {
      // Anonymous users can only see system exercises
      return exercises.filter(exercise => !exercise.is_user_created)
    }

    // Authenticated users can see their own exercises + system exercises
    return exercises.filter(exercise =>
      !exercise.is_user_created || exercise.created_by_user_id === userId
    )
  }

  /**
   * Apply all non-name filters (body_part, modality, is_user_created, created_by_user_id)
   */
  private applyNonNameFilters(
    exercises: ExerciseResponse[],
    filters: ExerciseFilters
  ): ExerciseResponse[] {
    let filtered = exercises

    // Filter by body_part
    if (filters.body_part) {
      const bodyPartQuery = filters.body_part.toLowerCase().trim()
      filtered = filtered.filter(exercise =>
        exercise.body_part.toLowerCase().includes(bodyPartQuery)
      )
    }

    // Filter by modality
    if (filters.modality) {
      const modalityQuery = filters.modality.toUpperCase() as ExerciseModality
      filtered = filtered.filter(exercise => exercise.modality === modalityQuery)
    }

    // Filter by is_user_created
    if (filters.is_user_created !== null && filters.is_user_created !== undefined) {
      filtered = filtered.filter(exercise =>
        exercise.is_user_created === filters.is_user_created
      )
    }

    // Filter by created_by_user_id
    if (filters.created_by_user_id) {
      filtered = filtered.filter(exercise =>
        exercise.created_by_user_id === filters.created_by_user_id
      )
    }

    return filtered
  }

  /**
   * Apply name filtering with different strategies based on query length
   * Replicates backend logic exactly:
   * - No name filter: Return all exercises
   * - Short queries (< 4 chars): Simple includes matching
   * - Long queries (>= 4 chars): Fuzzy matching with Fuse.js
   */
  private applyNameFilter(
    exercises: ExerciseResponse[],
    nameQuery?: string | null
  ): ExerciseResponse[] {
    if (!nameQuery) {
      // No name filter - return all exercises sorted by name
      return exercises.sort((a, b) => a.name.localeCompare(b.name))
    }

    const trimmedQuery = nameQuery.trim()

    if (trimmedQuery.length < 4) {
      // Short query - use simple includes matching (case-insensitive)
      return exercises
        .filter(exercise =>
          exercise.name.toLowerCase().includes(trimmedQuery.toLowerCase())
        )
        .sort((a, b) => a.name.localeCompare(b.name))
    } else {
      // Long query - use fuzzy matching with Fuse.js
      if (!this.fuse) {
        return exercises
      }

      // Create a temporary Fuse instance with the filtered exercises
      const tempFuse = new Fuse(exercises, {
        keys: ['name'],
        threshold: 0.3,
        distance: 100,
        minMatchCharLength: 1,
        includeScore: true,
      })

      const fuseResults = tempFuse.search(trimmedQuery)

      // Extract exercises from Fuse results (they're already sorted by score)
      return fuseResults.map(result => result.item)
    }
  }

  /**
   * Get distinct body parts from the current exercise dataset
   */
  getDistinctBodyParts(userId?: number | null): string[] {
    const filteredExercises = this.applyPermissionFilter(this.exercises, userId)
    const bodyParts = Array.from(
      new Set(
        filteredExercises
          .map(exercise => exercise.body_part)
          .filter(bodyPart => bodyPart && bodyPart.trim().length > 0)
      )
    )
    return bodyParts.sort()
  }

  /**
   * Get exercises by body part
   */
  getByBodyPart(
    bodyPart: string,
    pagination: Pagination,
    userId?: number | null
  ): SearchResult {
    const filters: ExerciseFilters = { body_part: bodyPart }
    return this.search(filters, pagination, userId)
  }

  /**
   * Get exercises by modality
   */
  getByModality(
    modality: string,
    pagination: Pagination,
    userId?: number | null
  ): SearchResult {
    const filters: ExerciseFilters = { modality }
    return this.search(filters, pagination, userId)
  }

  /**
   * Get user's own exercises
   */
  getUserExercises(userId: number, pagination: Pagination): SearchResult {
    const filters: ExerciseFilters = {
      created_by_user_id: userId,
      is_user_created: true
    }
    return this.search(filters, pagination, userId)
  }

  /**
   * Get system exercises
   */
  getSystemExercises(pagination: Pagination): SearchResult {
    const filters: ExerciseFilters = { is_user_created: false }
    return this.search(filters, pagination)
  }
}
