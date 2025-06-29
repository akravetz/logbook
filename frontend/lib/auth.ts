import { NextAuthOptions } from "next-auth"
import GoogleProvider from "next-auth/providers/google"
import CredentialsProvider from "next-auth/providers/credentials"

// Build providers array based on environment
const providers: any[] = [
  GoogleProvider({
    clientId: process.env.GOOGLE_CLIENT_ID!,
    clientSecret: process.env.GOOGLE_CLIENT_SECRET!,
  }),
]

// Add CredentialsProvider for development mode
if (process.env.NODE_ENV === 'development' && process.env.NEXT_PUBLIC_ENABLE_DEV_AUTH === 'true') {
  providers.push(
    CredentialsProvider({
      id: 'dev-login',
      name: 'Development Login',
      credentials: {
        email: {
          label: "Email",
          type: "email",
          placeholder: "Enter any email address"
        }
      },
      async authorize(credentials) {
        if (!credentials?.email) {
          return null
        }

        try {
          // Call our backend dev-login endpoint
          const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8080'}/api/v1/auth/dev-login`, {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
            },
            body: JSON.stringify({
              email: credentials.email,
              name: credentials.email.split('@')[0], // Generate name from email
            }),
          })

          if (!response.ok) {
            console.error('Development login failed:', response.status, response.statusText)
            return null
          }

          const data = await response.json()

          // Return user data in format expected by NextAuth
          return {
            id: data.user.id.toString(),
            email: data.user.email_address,
            name: data.user.name,
            image: data.user.profile_image_url,
            accessToken: data.tokens.access_token,
            refreshToken: data.tokens.refresh_token,
            isDev: true, // Flag to identify dev users
          }
        } catch (error) {
          console.error('Error during development login:', error)
          return null
        }
      }
    })
  )
}

export const authOptions: NextAuthOptions = {
  providers,
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
        // Development login - tokens are already set by authorize function
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
        token.isDev = user.isDev || false
      }

      return token
    },
    async session({ session, token }) {
      // Send properties to the client
      session.accessToken = token.accessToken as string
      session.refreshToken = token.refreshToken as string
      session.userId = token.userId as string
      session.isDev = token.isDev as boolean

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
