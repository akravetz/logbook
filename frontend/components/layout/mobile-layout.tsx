"use client"

import { ReactNode } from 'react'
import { usePathname } from 'next/navigation'
import { useSession } from 'next-auth/react'
import { BottomNav } from './bottom-nav'
import { cn } from '@/lib/utils'

interface MobileLayoutProps {
  children: ReactNode
  showBottomNav?: boolean
}

export function MobileLayout({ children, showBottomNav = true }: MobileLayoutProps) {
  const pathname = usePathname()
  const { data: session } = useSession()

  // Hide bottom nav when not authenticated, on login page, or when explicitly disabled
  const shouldShowBottomNav = session && showBottomNav && pathname !== '/login'

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Main content area with padding for bottom nav */}
      <main className={cn(
        "min-h-screen",
        shouldShowBottomNav && "pb-20"
      )}>
        {children}
      </main>

      {/* Bottom navigation */}
      {shouldShowBottomNav && <BottomNav />}
    </div>
  )
}
