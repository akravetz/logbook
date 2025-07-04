import NextAuth from "next-auth"
import { JWT } from "next-auth/jwt"

declare module "next-auth" {
  interface Session {
    sessionToken: string
    userId: string
  }

  interface User {
    sessionToken?: string
  }
}

declare module "next-auth/jwt" {
  interface JWT {
    sessionToken?: string
    userId?: string
  }
}
