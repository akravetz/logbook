"use client"

import type React from "react"
import { createContext, useContext, useState, useEffect, useCallback } from "react"

interface ActiveSet {
  weight: number
  clean_reps: number
  forced_reps: number
}

interface ActiveExercise {
  exercise_id: number
  exercise_name: string
  sets: ActiveSet[]
  currentSet: ActiveSet
}

interface WorkoutContextType {
  activeWorkout: any | null
  currentExercise: ActiveExercise | null
  workoutTimer: number
  isWorkoutActive: boolean
  startWorkout: () => void
  finishWorkout: () => void
  addExercise: (exercise: any) => void
  updateCurrentSet: (set: Partial<ActiveSet>) => void
  completeSet: () => void
  startTimer: () => void
  stopTimer: () => void
}

const WorkoutContext = createContext<WorkoutContextType | undefined>(undefined)

export function WorkoutProvider({ children }: { children: React.ReactNode }) {
  const [activeWorkout, setActiveWorkout] = useState<any | null>(null)
  const [currentExercise, setCurrentExercise] = useState<ActiveExercise | null>(null)
  const [workoutTimer, setWorkoutTimer] = useState(0)
  const [isWorkoutActive, setIsWorkoutActive] = useState(false)
  const [timerInterval, setTimerInterval] = useState<NodeJS.Timeout | null>(null)
  const [mounted, setMounted] = useState(false)

  useEffect(() => {
    setMounted(true)
  }, [])

  const stopTimer = useCallback(() => {
    if (timerInterval) {
      clearInterval(timerInterval)
      setTimerInterval(null)
    }
  }, [timerInterval])

  const startTimer = useCallback(() => {
    if (!mounted) return
    stopTimer() // Clear any existing timer
    const interval = setInterval(() => {
      setWorkoutTimer((prev) => prev + 1)
    }, 1000)
    setTimerInterval(interval)
  }, [stopTimer, mounted])

  useEffect(() => {
    return () => {
      if (timerInterval) {
        clearInterval(timerInterval)
      }
    }
  }, [timerInterval])

  const startWorkout = useCallback(() => {
    if (!mounted) return
    setIsWorkoutActive(true)
    setWorkoutTimer(0)
    startTimer()
  }, [startTimer, mounted])

  const finishWorkout = useCallback(() => {
    if (!mounted) return
    setIsWorkoutActive(false)
    setActiveWorkout(null)
    setCurrentExercise(null)
    stopTimer()
    setWorkoutTimer(0)
  }, [stopTimer, mounted])

  const addExercise = useCallback(
    (exercise: any) => {
      if (!mounted) return
      setCurrentExercise({
        exercise_id: exercise.id,
        exercise_name: exercise.name,
        sets: [],
        currentSet: { weight: 0, clean_reps: 0, forced_reps: 0 },
      })
    },
    [mounted],
  )

  const updateCurrentSet = useCallback(
    (setUpdate: Partial<ActiveSet>) => {
      if (!mounted) return
      setCurrentExercise((prev) => {
        if (!prev) return prev
        return {
          ...prev,
          currentSet: { ...prev.currentSet, ...setUpdate },
        }
      })
    },
    [mounted],
  )

  const completeSet = useCallback(() => {
    if (!mounted) return
    setCurrentExercise((prev) => {
      if (!prev) return prev
      const newSets = [...prev.sets, prev.currentSet]
      return {
        ...prev,
        sets: newSets,
        currentSet: { ...prev.currentSet, forced_reps: 0 }, // Reset forced reps for next set
      }
    })
  }, [mounted])

  // Don't render anything until mounted
  if (!mounted) {
    return null
  }

  return (
    <WorkoutContext.Provider
      value={{
        activeWorkout,
        currentExercise,
        workoutTimer,
        isWorkoutActive,
        startWorkout,
        finishWorkout,
        addExercise,
        updateCurrentSet,
        completeSet,
        startTimer,
        stopTimer,
      }}
    >
      {children}
    </WorkoutContext.Provider>
  )
}

export function useWorkout() {
  const context = useContext(WorkoutContext)
  if (context === undefined) {
    throw new Error("useWorkout must be used within a WorkoutProvider")
  }
  return context
}
