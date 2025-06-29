"use client"

import React, { useState, useEffect } from "react"
import { Inter } from "next/font/google"
import "./globals.css"
import { AuthProvider } from "@/lib/contexts/auth-context"
import { WorkoutProvider } from "@/lib/contexts/workout-context"
import { ThemeProvider } from "@/components/theme-provider"
import { QueryClient, QueryClientProvider } from "@tanstack/react-query"

const inter = Inter({ subsets: ["latin"] })

export default function ClientLayout({
  children,
}: {
  children: React.ReactNode
}) {
  const [queryClient] = useState(
    () =>
      new QueryClient({
        defaultOptions: {
          queries: {
            staleTime: 60 * 1000,
            retry: 1,
          },
        },
      }),
  )

  const [mounted, setMounted] = useState(false)

  useEffect(() => {
    setMounted(true)
  }, [])

  if (!mounted) {
    return (
      <html lang="en">
        <body className={inter.className}>
          <div className="min-h-screen flex items-center justify-center bg-background">
            <div className="w-8 h-8 border-2 border-primary border-t-transparent rounded-full animate-spin" />
          </div>
        </body>
      </html>
    )
  }

  return (
    <html lang="en" suppressHydrationWarning>
      <body className={inter.className}>
        <QueryClientProvider client={queryClient}>
          <ThemeProvider attribute="class" defaultTheme="dark" enableSystem={false} disableTransitionOnChange>
            <AuthProvider>
              <WorkoutProvider>{children}</WorkoutProvider>
            </AuthProvider>
          </ThemeProvider>
        </QueryClientProvider>
      </body>
    </html>
  )
}
