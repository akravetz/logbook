import NextAuth from "next-auth"
import { JWT } from "next-auth/jwt"

declare module "next-auth" {
  interface Session {
    accessToken: string
    refreshToken: string
    userId: string
    isDev?: boolean
  }

  interface User {
    accessToken?: string
    refreshToken?: string
    isDev?: boolean
  }
}

declare module "next-auth/jwt" {
  interface JWT {
    accessToken?: string
    refreshToken?: string
    userId?: string
    isDev?: boolean
  }
}
