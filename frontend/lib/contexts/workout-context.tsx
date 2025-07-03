"use client"

import React from "react"

// Simple provider component since we're using Zustand for state management
export function WorkoutProvider({ children }: { children: React.ReactNode }) {
  return <>{children}</>
}
