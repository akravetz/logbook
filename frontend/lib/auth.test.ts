import { authOptions } from './auth'
import { verifyAuthTokenApiV1AuthVerifyTokenPost } from '@/lib/api/generated'
import type { AuthTokenRequest, AuthTokenResponse } from '@/lib/api/model'

// Mock the API function
jest.mock('@/lib/api/generated', () => ({
  verifyAuthTokenApiV1AuthVerifyTokenPost: jest.fn(),
}))

describe('Auth Configuration', () => {
  const mockVerifyAuthToken = verifyAuthTokenApiV1AuthVerifyTokenPost as jest.MockedFunction<
    typeof verifyAuthTokenApiV1AuthVerifyTokenPost
  >

  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('should have correct auth configuration structure', () => {
    expect(authOptions).toHaveProperty('providers')
    expect(authOptions).toHaveProperty('callbacks')
    expect(authOptions).toHaveProperty('session')
    expect(authOptions.session?.strategy).toBe('jwt')
    expect(authOptions.session?.maxAge).toBe(6 * 60 * 60) // 6 hours
  })

  it('should use generated API for token verification', async () => {
    const mockResponse: AuthTokenResponse = {
      session_token: 'mock-session-token',
      user: {
        id: 123,
        email: 'test@example.com',
        name: 'Test User',
        image: 'https://example.com/avatar.jpg',
      },
    }

    mockVerifyAuthToken.mockResolvedValue(mockResponse)

    const signInCallback = authOptions.callbacks?.signIn
    expect(signInCallback).toBeDefined()

    if (signInCallback) {
      const mockUser = { id: '', email: 'test@example.com', sessionToken: undefined as string | undefined }
      const mockAccount = {
        provider: 'google' as const,
        access_token: 'mock-google-token',
        providerAccountId: 'google-account-id',
        type: 'oauth' as const,
      }

      const result = await signInCallback({
        user: mockUser,
        account: mockAccount,
        profile: {},
      })

      expect(result).toBe(true)
      expect(mockVerifyAuthToken).toHaveBeenCalledWith({
        access_token: 'mock-google-token',
      } as AuthTokenRequest)
      expect(mockUser.sessionToken).toBe('mock-session-token')
      expect(mockUser.id).toBe('123')
    }
  })

  it('should handle API errors gracefully', async () => {
    const consoleSpy = jest.spyOn(console, 'error').mockImplementation(() => {})
    mockVerifyAuthToken.mockRejectedValue(new Error('API Error'))

    const signInCallback = authOptions.callbacks?.signIn
    expect(signInCallback).toBeDefined()

    if (signInCallback) {
      const mockUser = { id: '', email: 'test@example.com', sessionToken: undefined as string | undefined }
      const mockAccount = {
        provider: 'google' as const,
        access_token: 'mock-google-token',
        providerAccountId: 'google-account-id',
        type: 'oauth' as const,
      }

      const result = await signInCallback({
        user: mockUser,
        account: mockAccount,
        profile: {},
      })

      expect(result).toBe(false)
      expect(mockVerifyAuthToken).toHaveBeenCalledWith({
        access_token: 'mock-google-token',
      } as AuthTokenRequest)
    }

    consoleSpy.mockRestore()
  })

  it('should reject non-google providers', async () => {
    const signInCallback = authOptions.callbacks?.signIn
    expect(signInCallback).toBeDefined()

    if (signInCallback) {
      const mockUser = { id: '', email: 'test@example.com', sessionToken: undefined as string | undefined }
      const mockAccount = {
        provider: 'github' as const,
        access_token: 'mock-github-token',
        providerAccountId: 'github-account-id',
        type: 'oauth' as const,
      }

      const result = await signInCallback({
        user: mockUser,
        account: mockAccount,
        profile: {},
      })

      expect(result).toBe(false)
      expect(mockVerifyAuthToken).not.toHaveBeenCalled()
    }
  })
})
