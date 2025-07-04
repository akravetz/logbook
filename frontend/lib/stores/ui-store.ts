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
    selectExercise: boolean
    addNewExercise: boolean
    addSet: { open: boolean; exerciseId: number | null }
    editSet: { open: boolean; exerciseId: number | null; setId: number | null; currentData?: any }
    voiceNote: { open: boolean; exerciseId: number | null; exerciseName: string | null }
  }

  // UI states
  selectedExerciseForSet: Exercise | null

  // Modal actions
  openSelectExerciseModal: () => void
  openAddNewExerciseModal: () => void
  openAddSetModal: (exerciseId: number, exercise: Exercise) => void
  openEditSetModal: (exerciseId: number, setId: number, currentData: any) => void
  openVoiceNoteModal: (exerciseId: number, exerciseName: string) => void
  closeAllModals: () => void

  // UI actions
  setSelectedExerciseForSet: (exercise: Exercise | null) => void
}

export const useUIStore = create<UIState>((set) => ({
  // Initial state
  modals: {
    selectExercise: false,
    addNewExercise: false,
    addSet: { open: false, exerciseId: null },
    editSet: { open: false, exerciseId: null, setId: null, currentData: null },
    voiceNote: { open: false, exerciseId: null, exerciseName: null },
  },
  selectedExerciseForSet: null,

  // Actions
  openSelectExerciseModal: () =>
    set((state) => ({
      modals: { ...state.modals, selectExercise: true },
    })),

  openAddNewExerciseModal: () =>
    set((state) => ({
      modals: { ...state.modals, addNewExercise: true },
    })),

  openAddSetModal: (exerciseId: number, exercise: Exercise) =>
    set({
      modals: {
        selectExercise: false,
        addNewExercise: false,
        addSet: { open: true, exerciseId },
        editSet: { open: false, exerciseId: null, setId: null },
        voiceNote: { open: false, exerciseId: null, exerciseName: null },
      },
      selectedExerciseForSet: exercise,
    }),

  openEditSetModal: (exerciseId: number, setId: number, currentData: any) =>
    set({
      modals: {
        selectExercise: false,
        addNewExercise: false,
        addSet: { open: false, exerciseId: null },
        editSet: { open: true, exerciseId, setId, currentData },
        voiceNote: { open: false, exerciseId: null, exerciseName: null },
      },
    }),

  openVoiceNoteModal: (exerciseId: number, exerciseName: string) =>
    set({
      modals: {
        selectExercise: false,
        addNewExercise: false,
        addSet: { open: false, exerciseId: null },
        editSet: { open: false, exerciseId: null, setId: null },
        voiceNote: { open: true, exerciseId, exerciseName },
      },
    }),

  closeAllModals: () =>
    set({
      modals: {
        selectExercise: false,
        addNewExercise: false,
        addSet: { open: false, exerciseId: null },
        editSet: { open: false, exerciseId: null, setId: null },
        voiceNote: { open: false, exerciseId: null, exerciseName: null },
      },
      selectedExerciseForSet: null,
    }),

  setSelectedExerciseForSet: (exercise: Exercise | null) =>
    set({ selectedExerciseForSet: exercise }),
}))
