import { NextAuthOptions } from "next-auth"
import GoogleProvider from "next-auth/providers/google"
import { createOAuthLogger, createConfigLogger } from './logger'
import { config, validateEnvironment } from './config'
import { randomUUID } from 'crypto'

// Validate environment on module load
try {
  validateEnvironment()
} catch (error) {
  const configLogger = createConfigLogger()
  configLogger.error({
    event: 'environment_validation_failed',
    error: error instanceof Error ? error.message : String(error)
  }, 'Critical environment variables missing')
  throw error
}

export const authOptions: NextAuthOptions = {
  // Enable NextAuth debug in development only
  debug: config.oauth.debug,

  // Custom logger for production
  logger: process.env.NODE_ENV === 'production' ? {
    error(code: string, metadata?: any) {
      const logger = createOAuthLogger('nextauth')
      logger.error({ code, metadata }, 'NextAuth error occurred')
    },
    warn(code: string, metadata?: any) {
      const logger = createOAuthLogger('nextauth')
      logger.warn({ code, metadata }, 'NextAuth warning')
    },
    debug(code: string, metadata?: any) {
      const logger = createOAuthLogger('nextauth')
      logger.debug({ code, metadata }, 'NextAuth debug')
    }
  } : undefined,

  providers: [
    GoogleProvider({
      clientId: process.env.GOOGLE_CLIENT_ID!,
      clientSecret: process.env.GOOGLE_CLIENT_SECRET!,
    }),
  ],
  callbacks: {
    async signIn({ user, account, profile }) {
      const requestId = randomUUID()
      const logger = createOAuthLogger('google', requestId)

      logger.info({
        event: 'signin_attempt',
        userId: user?.id,
        userEmail: user?.email,
        provider: account?.provider,
        // Safe account info (no tokens)
        accountType: account?.type,
        accountProvider: account?.provider,
        accountProviderAccountId: account?.providerAccountId,
                 // Profile info (non-sensitive)
         profileVerified: (profile as any)?.email_verified,
         profileLocale: (profile as any)?.locale,
        // Environment info
        environment: process.env.NODE_ENV,
        nextAuthUrl: process.env.NEXTAUTH_URL,
        apiUrl: config.api.baseUrl,
        timestamp: new Date().toISOString()
      }, 'Google OAuth sign-in attempt started')

      if (account?.provider === "google" && account.access_token) {
        try {
          logger.info({
            event: 'backend_verification_start',
            requestId,
            backendUrl: config.api.baseUrl,
            hasAccessToken: !!account.access_token,
            tokenLength: account.access_token?.length,
            accountScope: account.scope
          }, 'Starting backend token verification')

          const response = await fetch(
            `${config.api.baseUrl}/api/v1/auth/verify-token`,
            {
              method: "POST",
              headers: {
                "Content-Type": "application/json",
              },
              body: JSON.stringify({
                access_token: account.access_token,
              }),
            }
          )

          logger.info({
            event: 'backend_verification_response',
            requestId,
            statusCode: response.status,
            statusText: response.statusText,
            responseOk: response.ok,
            contentType: response.headers.get('content-type'),
            responseSize: response.headers.get('content-length'),
            responseHeaders: {
              'content-type': response.headers.get('content-type'),
              'cache-control': response.headers.get('cache-control'),
              'x-request-id': response.headers.get('x-request-id')
            }
          }, 'Backend verification response received')

          if (!response.ok) {
            let errorBody = ''
            try {
              errorBody = await response.text()
            } catch (e) {
              logger.warn({ requestId, parseError: String(e) }, 'Failed to parse error response body')
            }

            logger.error({
              event: 'backend_verification_failed',
              requestId,
              statusCode: response.status,
              statusText: response.statusText,
              errorBody: errorBody.substring(0, 1000), // Limit error body size
              environment: process.env.NODE_ENV,
              url: response.url,
              redirected: response.redirected
            }, 'Backend token verification failed')
            return false
          }

          const data = await response.json()

          logger.info({
            event: 'backend_verification_success',
            requestId,
            hasSessionToken: !!data.session_token,
            sessionTokenLength: data.session_token?.length,
            userId: data.user?.id,
            userEmail: data.user?.email,
            responseKeys: Object.keys(data)
          }, 'Backend verification successful')

          user.sessionToken = data.session_token
          user.id = data.user.id.toString()

          return true
        } catch (error) {
          logger.error({
            event: 'backend_verification_error',
            requestId,
            error: error instanceof Error ? {
                             name: error.name,
               message: error.message,
               stack: config.oauth.debug ? error.stack : undefined
            } : String(error),
            environment: process.env.NODE_ENV,
            backendUrl: config.api.baseUrl
          }, 'Error during backend token verification')
          return false
        }
      }

      logger.warn({
        event: 'signin_rejected',
        requestId,
        reason: 'not_google_provider_or_missing_token',
        provider: account?.provider,
        hasAccessToken: !!account?.access_token,
        accountType: account?.type
      }, 'Sign-in rejected')

      return false
    },
    async jwt({ token, user }) {
      if (user?.sessionToken) {
        const logger = createOAuthLogger('google')
        logger.debug({
          event: 'jwt_token_update',
          hasSessionToken: !!user.sessionToken,
          sessionTokenLength: user.sessionToken?.length,
          userId: user.id,
          existingTokenKeys: Object.keys(token)
        }, 'JWT token updated with session data')

        token.sessionToken = user.sessionToken
        token.userId = user.id
      }
      return token
    },
    async session({ session, token }) {
      const logger = createOAuthLogger('google')
      logger.debug({
        event: 'session_created',
        hasSessionToken: !!token.sessionToken,
        sessionTokenLength: typeof token.sessionToken === 'string' ? token.sessionToken.length : 0,
        userId: token.userId,
        userEmail: session.user?.email,
        sessionKeys: Object.keys(session),
        tokenKeys: Object.keys(token)
      }, 'Session created successfully')

      session.sessionToken = token.sessionToken as string
      session.userId = token.userId as string
      return session
    }
  },
  pages: {
    signIn: '/', // Redirect to home page for sign in
  },
  session: {
    strategy: 'jwt',
    // Set session max age to 6 hours to match backend token expiry
    maxAge: 6 * 60 * 60, // 6 hours
  },
  cookies: {
    sessionToken: {
      name: 'next-auth.session-token',
      options: {
        httpOnly: true,
        sameSite: 'lax',
        path: '/',
        secure: process.env.NODE_ENV === 'production'
      }
    }
  },
  secret: process.env.NEXTAUTH_SECRET,
}
