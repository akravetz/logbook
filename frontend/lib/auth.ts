import { NextAuthOptions } from "next-auth"
import GoogleProvider from "next-auth/providers/google"

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
          const response = await fetch(
            `${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8080"}/api/v1/auth/verify-token`,
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

          if (!response.ok) {
            // Log error for debugging in development
            if (process.env.NODE_ENV === 'development') {
              console.error("Backend token verification failed:", response.status, response.statusText)
            }
            return false
          }

          const data = await response.json()

          // Store the backend session token for API access
          user.sessionToken = data.session_token
          user.id = data.user.id.toString()

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
