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

                // Return user object with tokens
                return {
                  id: data.user.id.toString(),
                  email: data.user.email,
                  name: data.user.name,
                  image: data.user.image,
                  accessToken: data.tokens.access_token,
                  refreshToken: data.tokens.refresh_token,
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

          // Store JWT tokens in the user object for later use
          user.accessToken = data.tokens.access_token
          user.refreshToken = data.tokens.refresh_token
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
        token.accessToken = user.accessToken
        token.refreshToken = user.refreshToken
        token.userId = user.id
      }

      return token
    },
    async session({ session, token }) {
      // Send properties to the client
      session.accessToken = token.accessToken as string
      session.refreshToken = token.refreshToken as string
      session.userId = token.userId as string

      return session
    },
  },
  pages: {
    signIn: '/', // Redirect to home page for sign in
  },
  session: {
    strategy: 'jwt',
  },
  secret: process.env.NEXTAUTH_SECRET,
}
