import { useState, useEffect } from 'react'

interface VisualViewportState {
  isKeyboardVisible: boolean
  availableHeight: number
  keyboardHeight: number
  viewportHeight: number
  safeAreaTop: number
  safeAreaBottom: number
}

export function useVisualViewport(): VisualViewportState {
  const [viewportState, setViewportState] = useState<VisualViewportState>({
    isKeyboardVisible: false,
    availableHeight: 0,
    keyboardHeight: 0,
    viewportHeight: 0,
    safeAreaTop: 0,
    safeAreaBottom: 0,
  })

  useEffect(() => {
    // Check if Visual Viewport API is supported
    if (!window.visualViewport) {
      // Fallback for browsers without Visual Viewport API
      const fallbackHeight = window.innerHeight
      setViewportState({
        isKeyboardVisible: false,
        availableHeight: fallbackHeight,
        keyboardHeight: 0,
        viewportHeight: fallbackHeight,
        safeAreaTop: 0,
        safeAreaBottom: 0,
      })
      return
    }

    const updateViewportState = () => {
      const visualViewport = window.visualViewport!
      const documentHeight = document.documentElement.clientHeight

      // Calculate keyboard height (difference between document height and visual viewport height)
      const keyboardHeight = Math.max(0, documentHeight - visualViewport.height)
      const isKeyboardVisible = keyboardHeight > 150 // Threshold to detect keyboard (150px minimum)

      // Get safe area values from CSS environment variables
      const computedStyle = getComputedStyle(document.documentElement)
      const safeAreaTopStr = computedStyle.getPropertyValue('env(safe-area-inset-top)')
      const safeAreaBottomStr = computedStyle.getPropertyValue('env(safe-area-inset-bottom)')
      const safeAreaTop = safeAreaTopStr ? parseInt(safeAreaTopStr.replace('px', '')) : 0
      const safeAreaBottom = safeAreaBottomStr ? parseInt(safeAreaBottomStr.replace('px', '')) : 0

      setViewportState({
        isKeyboardVisible,
        availableHeight: visualViewport.height,
        keyboardHeight,
        viewportHeight: documentHeight,
        safeAreaTop,
        safeAreaBottom,
      })
    }

    // Initial state
    updateViewportState()

    // Listen for viewport changes
    window.visualViewport.addEventListener('resize', updateViewportState)
    window.visualViewport.addEventListener('scroll', updateViewportState)

    // Cleanup
    return () => {
      window.visualViewport?.removeEventListener('resize', updateViewportState)
      window.visualViewport?.removeEventListener('scroll', updateViewportState)
    }
  }, [])

  return viewportState
}

// Visual Viewport API is already defined in TypeScript DOM types
