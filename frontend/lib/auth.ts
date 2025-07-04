import { NextAuthOptions } from "next-auth"
import GoogleProvider from "next-auth/providers/google"
import CredentialsProvider from "next-auth/providers/credentials"

export const authOptions: NextAuthOptions = {
  providers: [
    GoogleProvider({
      clientId: process.env.GOOGLE_CLIENT_ID!,
      clientSecret: process.env.GOOGLE_CLIENT_SECRET!,
    }),
    // Development-only credentials provider
    ...(process.env.NODE_ENV === "development"
      ? [
          CredentialsProvider({
            id: "dev-login",
            name: "Development Login",
            credentials: {
              email: {
                label: "Email",
                type: "email",
                placeholder: "developer@example.com",
              },
            },
            async authorize(credentials) {
              if (!credentials?.email) {
                return null
              }

              try {
                // Call our backend dev login endpoint
                const response = await fetch(
                  `${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8080"}/api/v1/auth/dev-login`,
                  {
                    method: "POST",
                    headers: {
                      "Content-Type": "application/json",
                    },
                    body: JSON.stringify({
                      email: credentials.email,
                    }),
                  }
                )

                if (!response.ok) {
                  console.error("Dev login failed:", response.status, response.statusText)
                  return null
                }

                const data = await response.json()

                // Convert ISO timestamp to Unix timestamp for NextAuth
                const expiresAt = Math.floor(new Date(data.tokens.expires_at).getTime() / 1000)

                // Return user object with tokens
                return {
                  id: data.user.id.toString(),
                  email: data.user.email,
                  name: data.user.name,
                  image: data.user.image,
                  accessToken: data.tokens.access_token,
                  refreshToken: data.tokens.refresh_token,
                  tokenExpiresAt: expiresAt,
                }
              } catch (error) {
                console.error("Error during dev login:", error)
                return null
              }
            },
          }),
        ]
      : []),
  ],
  callbacks: {
    async signIn({ user, account, profile }) {
      if (account?.provider === "google") {
        try {
          // Call our backend to verify/create user and get JWT tokens
          const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8080'}/api/v1/auth/verify-google-user`, {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
            },
            body: JSON.stringify({
              email: user.email,
              name: user.name,
              image: user.image,
              email_verified: true,
            }),
          })

          if (!response.ok) {
            console.error('Backend user verification failed:', response.status, response.statusText)
            return false
          }

          const data = await response.json()

          // Convert ISO timestamp to Unix timestamp for NextAuth
          const expiresAt = Math.floor(new Date(data.tokens.expires_at).getTime() / 1000)

          // Store JWT tokens in the user object for later use
          user.accessToken = data.tokens.access_token
          user.refreshToken = data.tokens.refresh_token
          user.tokenExpiresAt = expiresAt
          user.id = data.user.id.toString()

          return true
        } catch (error) {
          console.error('Error verifying user with backend:', error)
          return false
        }
      } else if (account?.provider === "dev-login") {
        // Dev login already handled in authorize function
        // Tokens are already attached to user object
        return true
      }
      return true
    },
    async jwt({ token, user, account }) {
      // Initial sign in
      if (account && user) {
        console.log("JWT: Initial sign in, setting tokens")
        return {
          ...token,
          accessToken: user.accessToken,
          refreshToken: user.refreshToken,
          tokenExpiresAt: user.tokenExpiresAt,
          userId: user.id,
        }
      }

      // Check if token should be refreshed
      // Refresh if token has expired OR expires in less than 5 minutes
      const currentTime = Date.now()
      const expirationTime = token.tokenExpiresAt ? (token.tokenExpiresAt as number) * 1000 : 0
      const timeUntilExpiry = expirationTime - currentTime
      const shouldRefresh = token.tokenExpiresAt
        ? expirationTime < currentTime + 5 * 60 * 1000  // Expires in less than 5 minutes OR already expired
        : false

      console.log("JWT callback debug:", {
        hasToken: !!token.tokenExpiresAt,
        currentTime: new Date(currentTime).toISOString(),
        expirationTime: new Date(expirationTime).toISOString(),
        timeUntilExpiryMinutes: Math.round(timeUntilExpiry / 1000 / 60),
        isExpired: expirationTime < currentTime,
        shouldRefresh,
        hasRefreshToken: !!token.refreshToken
      })

      if (shouldRefresh && token.refreshToken) {
        try {
          console.log("JWT: Token expiring soon, refreshing...")

          const response = await fetch(
            `${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8080"}/api/v1/auth/refresh`,
            {
              method: "POST",
              headers: {
                "Content-Type": "application/json",
              },
              body: JSON.stringify({
                refresh_token: token.refreshToken,
              }),
            }
          )

          if (!response.ok) {
            throw new Error(`Refresh failed: ${response.status}`)
          }

          const refreshedTokens = await response.json()

          // Convert ISO timestamp to Unix timestamp for NextAuth
          const newExpiresAt = Math.floor(new Date(refreshedTokens.expires_at).getTime() / 1000)

          console.log("JWT: Token refreshed successfully", {
            newExpiresAt: new Date(newExpiresAt * 1000).toISOString()
          })

          return {
            ...token,
            accessToken: refreshedTokens.access_token,
            refreshToken: refreshedTokens.refresh_token,
            tokenExpiresAt: newExpiresAt,
            error: undefined, // Clear any previous errors
          }
        } catch (error) {
          console.error("JWT: Error refreshing access token:", error)
          // Return token with error flag
          return {
            ...token,
            error: "RefreshTokenError",
          }
        }
      }

      return token
    },
    async session({ session, token }) {
      // Send properties to the client
      session.accessToken = token.accessToken as string
      session.refreshToken = token.refreshToken as string
      session.userId = token.userId as string
      session.error = token.error as "RefreshTokenError" | undefined

      return session
    },
  },
  pages: {
    signIn: '/', // Redirect to home page for sign in
  },
  session: {
    strategy: 'jwt',
    // Set session max age to 7 days to match refresh token
    maxAge: 7 * 24 * 60 * 60,
  },
  secret: process.env.NEXTAUTH_SECRET,
}
