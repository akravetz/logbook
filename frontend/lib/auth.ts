import { NextAuthOptions } from "next-auth"
import GoogleProvider from "next-auth/providers/google"
import { verifyAuthTokenApiV1AuthVerifyTokenPost } from "@/lib/api/generated"
import type { AuthTokenRequest, AuthTokenResponse } from "@/lib/api/model"
import { logger } from "@/lib/logger"

// Debug API configuration at module load
logger.debug("🔧 Auth module loaded - API Configuration:", {
  NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL,
  NODE_ENV: process.env.NODE_ENV,
  NEXTAUTH_URL: process.env.NEXTAUTH_URL,
})

export const authOptions: NextAuthOptions = {
  providers: [
    GoogleProvider({
      clientId: process.env.GOOGLE_CLIENT_ID!,
      clientSecret: process.env.GOOGLE_CLIENT_SECRET!,
    }),
  ],
  callbacks: {
    async signIn({ user, account }) {
      logger.debug("🔍 SignIn callback started", {
        provider: account?.provider,
        hasAccessToken: !!account?.access_token,
        userId: user?.id,
        userEmail: user?.email,
      })

      if (account?.provider === "google" && account.access_token) {
        try {
          logger.debug("🚀 Starting Google token verification", {
            apiUrl: process.env.NEXT_PUBLIC_API_URL,
            accessTokenLength: account.access_token.length,
          })

          // Send Google's access_token to backend for secure verification
          const authTokenRequest: AuthTokenRequest = {
            access_token: account.access_token,
          }

          logger.debug("📤 Making API request to verify token...")
          const response = await verifyAuthTokenApiV1AuthVerifyTokenPost(authTokenRequest)
          logger.debug("✅ API response received", {
            hasSessionToken: !!response.session_token,
            userId: response.user.id,
            userEmail: response.user.email,
          })

          // Store the backend session token for API access
          user.sessionToken = response.session_token
          user.id = response.user.id.toString()

          logger.debug("✅ SignIn callback successful")
          return true
        } catch (error) {
          logger.error("❌ Error in signIn callback:", {
            error: error instanceof Error ? error.message : String(error),
            stack: error instanceof Error ? error.stack : undefined,
            apiUrl: process.env.NEXT_PUBLIC_API_URL,
            provider: account?.provider,
          })
          return false
        }
      }

      logger.debug("❌ SignIn callback rejected - invalid provider or missing token")
      return false
    },
    async jwt({ token, user }) {
      logger.debug("🔑 JWT callback", {
        hasUser: !!user,
        hasUserSessionToken: !!user?.sessionToken,
        hasTokenSessionToken: !!token.sessionToken,
        userId: user?.id || token.userId,
      })

      // Store session token from sign in
      if (user?.sessionToken) {
        token.sessionToken = user.sessionToken
        token.userId = user.id
        logger.debug("✅ JWT token updated with session data")
      }
      return token
    },
    async session({ session, token }) {
      logger.debug("📋 Session callback", {
        hasTokenSessionToken: !!token.sessionToken,
        hasTokenUserId: !!token.userId,
        userEmail: session.user?.email,
      })

      // Send session token to client for API calls
      session.sessionToken = token.sessionToken as string
      session.userId = token.userId as string

      logger.debug("✅ Session data prepared for client")
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
