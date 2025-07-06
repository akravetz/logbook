import { type Metadata, type Viewport } from "next"
import { Geist } from "next/font/google"
import "./globals.css"
import { ThemeProvider } from "@/components/theme-provider"
import { AuthProvider } from "@/lib/contexts/auth-context"
import { WorkoutProvider } from "@/lib/contexts/workout-context"
import { ReactQueryProvider } from "@/lib/react-query"
import { MobileLayout } from "@/components/layout/mobile-layout"
import { Toaster } from "sonner"

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
})

export const metadata: Metadata = {
  title: "Get Swole",
  description: "Your personal workout tracking companion",
}

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  maximumScale: 1,
  userScalable: false,
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className={`${geistSans.variable} font-sans`}>
        <ReactQueryProvider>
          <ThemeProvider attribute="class" defaultTheme="light" enableSystem={false} disableTransitionOnChange>
            <AuthProvider>
              <WorkoutProvider>
                <MobileLayout>
                  {children}
                </MobileLayout>
                <Toaster position="bottom-right" />
              </WorkoutProvider>
            </AuthProvider>
          </ThemeProvider>
        </ReactQueryProvider>
      </body>
    </html>
  )
}
