import '@testing-library/jest-dom'

// Add any global test configuration here
// For example:
// - Global mocks
// - Test utilities
// - Custom matchers

// Mock Next.js router if needed in tests
jest.mock('next/router', () => ({
  useRouter: jest.fn(),
  push: jest.fn(),
  replace: jest.fn(),
  back: jest.fn(),
  forward: jest.fn(),
  reload: jest.fn(),
}))

// Mock next/navigation for app router
jest.mock('next/navigation', () => ({
  useRouter: jest.fn(),
  useSearchParams: jest.fn(),
  usePathname: jest.fn(),
  useParams: jest.fn(),
  redirect: jest.fn(),
  notFound: jest.fn(),
}))

// Set up global test environment
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: jest.fn().mockImplementation(query => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: jest.fn(), // deprecated
    removeListener: jest.fn(), // deprecated
    addEventListener: jest.fn(),
    removeEventListener: jest.fn(),
    dispatchEvent: jest.fn(),
  })),
})
