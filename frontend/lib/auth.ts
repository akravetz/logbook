import { NextAuthOptions } from "next-auth"
import GoogleProvider from "next-auth/providers/google"
import { verifyAuthTokenApiV1AuthVerifyTokenPost } from "@/lib/api/generated"
import type { AuthTokenRequest, AuthTokenResponse } from "@/lib/api/model"

export const authOptions: NextAuthOptions = {
  providers: [
    GoogleProvider({
      clientId: process.env.GOOGLE_CLIENT_ID!,
      clientSecret: process.env.GOOGLE_CLIENT_SECRET!,
    }),
  ],
  callbacks: {
    async signIn({ user, account }) {
      if (account?.provider === "google" && account.access_token) {
        try {
          // Send Google's access_token to backend for secure verification
          const authTokenRequest: AuthTokenRequest = {
            access_token: account.access_token,
          }

          const response = await verifyAuthTokenApiV1AuthVerifyTokenPost(authTokenRequest)

          // Store the backend session token for API access
          user.sessionToken = response.session_token
          user.id = response.user.id.toString()

          return true
        } catch (error) {
          // Log error for debugging in development
          if (process.env.NODE_ENV === 'development') {
            console.error("Error verifying Google token with backend:", error)
          }
          return false
        }
      }
      return false
    },
    async jwt({ token, user }) {
      // Store session token from sign in
      if (user?.sessionToken) {
        token.sessionToken = user.sessionToken
        token.userId = user.id
      }
      return token
    },
    async session({ session, token }) {
      // Send session token to client for API calls
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
