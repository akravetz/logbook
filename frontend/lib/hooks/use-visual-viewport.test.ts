import { renderHook } from '@testing-library/react'
import { useVisualViewport } from './use-visual-viewport'

// Ensure Jest types are available
/// <reference types="jest" />

// Mock the Visual Viewport API
const mockVisualViewport = {
  height: 600,
  width: 400,
  offsetTop: 0,
  offsetLeft: 0,
  pageTop: 0,
  pageLeft: 0,
  scale: 1,
  addEventListener: jest.fn(),
  removeEventListener: jest.fn(),
}

describe('useVisualViewport', () => {
  beforeEach(() => {
    // Reset mocks
    jest.clearAllMocks()

    // Mock document.documentElement.clientHeight
    Object.defineProperty(document.documentElement, 'clientHeight', {
      value: 800,
      writable: true,
    })

    // Mock getComputedStyle
    global.getComputedStyle = jest.fn().mockReturnValue({
      getPropertyValue: jest.fn().mockReturnValue(''),
    })
  })

  it('should return correct initial state with Visual Viewport API', () => {
    // Mock window.visualViewport with height closer to document height to simulate no keyboard
    const noKeyboardViewport = {
      ...mockVisualViewport,
      height: 750, // Close to document height (800) to simulate no keyboard
    }

    Object.defineProperty(window, 'visualViewport', {
      value: noKeyboardViewport,
      writable: true,
    })

    const { result } = renderHook(() => useVisualViewport())

    expect(result.current).toEqual({
      isKeyboardVisible: false,
      availableHeight: 750,
      keyboardHeight: 50, // 800 - 750 (below 150px threshold)
      viewportHeight: 800,
      safeAreaTop: 0,
      safeAreaBottom: 0,
    })
  })

  it('should detect keyboard visibility when height difference exceeds threshold', () => {
    // Simulate keyboard visible scenario
    const keyboardVisibleViewport = {
      ...mockVisualViewport,
      height: 400, // Smaller height simulating keyboard
    }

    Object.defineProperty(window, 'visualViewport', {
      value: keyboardVisibleViewport,
      writable: true,
    })

    const { result } = renderHook(() => useVisualViewport())

    expect(result.current.isKeyboardVisible).toBe(true)
    expect(result.current.keyboardHeight).toBe(400) // 800 - 400
  })

  it('should fallback when Visual Viewport API is not available', () => {
    // Remove Visual Viewport API
    Object.defineProperty(window, 'visualViewport', {
      value: undefined,
      writable: true,
    })

    // Mock window.innerHeight
    Object.defineProperty(window, 'innerHeight', {
      value: 800,
      writable: true,
    })

    const { result } = renderHook(() => useVisualViewport())

    expect(result.current).toEqual({
      isKeyboardVisible: false,
      availableHeight: 800,
      keyboardHeight: 0,
      viewportHeight: 800,
      safeAreaTop: 0,
      safeAreaBottom: 0,
    })
  })

  it('should handle safe area values correctly', () => {
    Object.defineProperty(window, 'visualViewport', {
      value: mockVisualViewport,
      writable: true,
    })

    // Mock getComputedStyle to return safe area values
    global.getComputedStyle = jest.fn().mockReturnValue({
      getPropertyValue: jest.fn().mockImplementation((prop: string) => {
        if (prop === 'env(safe-area-inset-top)') return '44px'
        if (prop === 'env(safe-area-inset-bottom)') return '34px'
        return ''
      }),
    })

    const { result } = renderHook(() => useVisualViewport())

    expect(result.current.safeAreaTop).toBe(44)
    expect(result.current.safeAreaBottom).toBe(34)
  })

  it('should register and cleanup event listeners', () => {
    Object.defineProperty(window, 'visualViewport', {
      value: mockVisualViewport,
      writable: true,
    })

    const { unmount } = renderHook(() => useVisualViewport())

    // Verify event listeners were added
    expect(mockVisualViewport.addEventListener).toHaveBeenCalledWith('resize', expect.any(Function))
    expect(mockVisualViewport.addEventListener).toHaveBeenCalledWith('scroll', expect.any(Function))

    // Unmount and verify cleanup
    unmount()

    expect(mockVisualViewport.removeEventListener).toHaveBeenCalledWith('resize', expect.any(Function))
    expect(mockVisualViewport.removeEventListener).toHaveBeenCalledWith('scroll', expect.any(Function))
  })
})
