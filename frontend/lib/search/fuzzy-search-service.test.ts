import { FuzzySearchService } from './fuzzy-search-service'
import type { ExerciseResponse } from '../api/model'

// Mock exercise data for testing
const mockExercises: ExerciseResponse[] = [
  {
    id: 1,
    name: 'Bench Press',
    body_part: 'chest',
    modality: 'BARBELL',
    is_user_created: false,
    created_at: '2023-01-01T00:00:00Z',
    updated_at: '2023-01-01T00:00:00Z',
  },
  {
    id: 2,
    name: 'Incline Dumbbell Press',
    body_part: 'chest',
    modality: 'DUMBBELL',
    is_user_created: false,
    created_at: '2023-01-01T00:00:00Z',
    updated_at: '2023-01-01T00:00:00Z',
  },
  {
    id: 3,
    name: 'Squat',
    body_part: 'legs',
    modality: 'BARBELL',
    is_user_created: false,
    created_at: '2023-01-01T00:00:00Z',
    updated_at: '2023-01-01T00:00:00Z',
  },
  {
    id: 4,
    name: 'Bicep Curl',
    body_part: 'arms',
    modality: 'DUMBBELL',
    is_user_created: true,
    created_by_user_id: 1,
    created_at: '2023-01-01T00:00:00Z',
    updated_at: '2023-01-01T00:00:00Z',
  },
  {
    id: 5,
    name: 'Deadlift',
    body_part: 'back',
    modality: 'BARBELL',
    is_user_created: false,
    created_at: '2023-01-01T00:00:00Z',
    updated_at: '2023-01-01T00:00:00Z',
  },
]

describe('FuzzySearchService', () => {
  let service: FuzzySearchService

  beforeEach(() => {
    service = new FuzzySearchService()
    service.setExercises(mockExercises)
  })

  describe('Permission filtering', () => {
    it('should show only system exercises for anonymous users', () => {
      const result = service.search(
        {},
        { page: 1, size: 10, offset: 0 },
        null // anonymous user
      )

      expect(result.items).toHaveLength(4) // All except the user-created one
      expect(result.items.every(ex => !ex.is_user_created)).toBe(true)
    })

    it('should show user exercises and system exercises for authenticated users', () => {
      const result = service.search(
        {},
        { page: 1, size: 10, offset: 0 },
        1 // user ID 1
      )

      expect(result.items).toHaveLength(5) // All exercises including user-created
      expect(result.items.some(ex => ex.is_user_created && ex.created_by_user_id === 1)).toBe(true)
    })
  })

  describe('Name filtering strategies', () => {
    it('should return all exercises when no name filter is provided', () => {
      const result = service.search(
        {},
        { page: 1, size: 10, offset: 0 },
        null
      )

      expect(result.items).toHaveLength(4) // System exercises only for anonymous
    })

    it('should use simple includes matching for short queries', () => {
      const result = service.search(
        { name: 'cur' }, // 3 characters
        { page: 1, size: 10, offset: 0 },
        1
      )

      expect(result.items).toHaveLength(1)
      expect(result.items[0].name).toBe('Bicep Curl')
    })

    it('should use fuzzy matching for long queries', () => {
      const result = service.search(
        { name: 'bench' }, // 5 characters
        { page: 1, size: 10, offset: 0 },
        null
      )

      expect(result.items).toHaveLength(1)
      expect(result.items[0].name).toBe('Bench Press')
    })

    it('should find fuzzy matches for misspelled queries', () => {
      const result = service.search(
        { name: 'benc' }, // Misspelled "bench"
        { page: 1, size: 10, offset: 0 },
        null
      )

      // Should still find "Bench Press" due to fuzzy matching
      expect(result.items).toHaveLength(1)
      expect(result.items[0].name).toBe('Bench Press')
    })
  })

  describe('Non-name filtering', () => {
    it('should filter by body part', () => {
      const result = service.search(
        { body_part: 'chest' },
        { page: 1, size: 10, offset: 0 },
        null
      )

      expect(result.items).toHaveLength(2)
      expect(result.items.every(ex => ex.body_part === 'chest')).toBe(true)
    })

    it('should filter by modality', () => {
      const result = service.search(
        { modality: 'DUMBBELL' },
        { page: 1, size: 10, offset: 0 },
        null
      )

      expect(result.items).toHaveLength(1) // Only system dumbbell exercises
      expect(result.items[0].name).toBe('Incline Dumbbell Press')
    })

    it('should filter by is_user_created', () => {
      const result = service.search(
        { is_user_created: false },
        { page: 1, size: 10, offset: 0 },
        1
      )

      expect(result.items).toHaveLength(4)
      expect(result.items.every(ex => !ex.is_user_created)).toBe(true)
    })
  })

  describe('Pagination', () => {
    it('should apply pagination correctly', () => {
      const result = service.search(
        {},
        { page: 1, size: 2, offset: 0 },
        null
      )

      expect(result.items).toHaveLength(2)
      expect(result.total).toBe(4)
      expect(result.pages).toBe(2)
      expect(result.page).toBe(1)
      expect(result.size).toBe(2)
    })

    it('should handle second page correctly', () => {
      const result = service.search(
        {},
        { page: 2, size: 2, offset: 2 },
        null
      )

      expect(result.items).toHaveLength(2)
      expect(result.total).toBe(4)
      expect(result.page).toBe(2)
    })
  })

  describe('Combined filtering', () => {
    it('should apply multiple filters together', () => {
      const result = service.search(
        {
          name: 'press',
          body_part: 'chest',
          modality: 'DUMBBELL'
        },
        { page: 1, size: 10, offset: 0 },
        null
      )

      expect(result.items).toHaveLength(1)
      expect(result.items[0].name).toBe('Incline Dumbbell Press')
    })
  })

  describe('Performance optimizations', () => {
    it('should not rebuild index when setExercises is called with same array reference', () => {
      const service = new FuzzySearchService()

      // Set exercises for the first time
      service.setExercises(mockExercises)

      // Mock the setCollection method to track calls
      const mockSetCollection = jest.fn()
      // Access the private fuse instance through type assertion
      const fuseInstance = (service as any).fuse
      if (fuseInstance) {
        fuseInstance.setCollection = mockSetCollection
      }

      // Call setExercises with the same array reference
      service.setExercises(mockExercises)

      // setCollection should not have been called again
      expect(mockSetCollection).not.toHaveBeenCalled()

      // Call setExercises with a different array (same content, different reference)
      const differentReferenceExercises = [...mockExercises]
      service.setExercises(differentReferenceExercises)

      // setCollection should have been called this time
      expect(mockSetCollection).toHaveBeenCalledWith(differentReferenceExercises)
    })
  })

  describe('Utility methods', () => {
    it('should get distinct body parts', () => {
      const bodyParts = service.getDistinctBodyParts(null)

      expect(bodyParts).toEqual(['back', 'chest', 'legs']) // Sorted, system exercises only
    })

    it('should get exercises by body part', () => {
      const result = service.getByBodyPart('chest', { page: 1, size: 10, offset: 0 }, null)

      expect(result.items).toHaveLength(2)
      expect(result.items.every(ex => ex.body_part === 'chest')).toBe(true)
    })

    it('should get system exercises', () => {
      const result = service.getSystemExercises({ page: 1, size: 10, offset: 0 })

      expect(result.items).toHaveLength(4)
      expect(result.items.every(ex => !ex.is_user_created)).toBe(true)
    })
  })
})
