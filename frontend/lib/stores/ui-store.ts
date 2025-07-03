import { create } from 'zustand'

interface Exercise {
  id: number
  name: string
  body_part: string
  modality: string
}

interface UIState {
  // Modal states
  modals: {
    addExercise: boolean
    addSet: { open: boolean; exerciseId: number | null }
    editSet: { open: boolean; exerciseId: number | null; setId: number | null; currentData?: any }
  }

  // UI states
  selectedExerciseForSet: Exercise | null

  // Modal actions
  openAddExerciseModal: () => void
  openAddSetModal: (exerciseId: number, exercise: Exercise) => void
  openEditSetModal: (exerciseId: number, setId: number, currentData: any) => void
  closeAllModals: () => void

  // UI actions
  setSelectedExerciseForSet: (exercise: Exercise | null) => void
}

export const useUIStore = create<UIState>((set) => ({
  // Initial state
  modals: {
    addExercise: false,
    addSet: { open: false, exerciseId: null },
    editSet: { open: false, exerciseId: null, setId: null, currentData: null },
  },
  selectedExerciseForSet: null,

  // Actions
  openAddExerciseModal: () =>
    set((state) => ({
      modals: { ...state.modals, addExercise: true },
    })),

  openAddSetModal: (exerciseId: number, exercise: Exercise) =>
    set({
      modals: {
        addExercise: false,
        addSet: { open: true, exerciseId },
        editSet: { open: false, exerciseId: null, setId: null },
      },
      selectedExerciseForSet: exercise,
    }),

  openEditSetModal: (exerciseId: number, setId: number, currentData: any) =>
    set({
      modals: {
        addExercise: false,
        addSet: { open: false, exerciseId: null },
        editSet: { open: true, exerciseId, setId, currentData },
      },
    }),

  closeAllModals: () =>
    set({
      modals: {
        addExercise: false,
        addSet: { open: false, exerciseId: null },
        editSet: { open: false, exerciseId: null, setId: null },
      },
      selectedExerciseForSet: null,
    }),

  setSelectedExerciseForSet: (exercise: Exercise | null) =>
    set({ selectedExerciseForSet: exercise }),
}))
