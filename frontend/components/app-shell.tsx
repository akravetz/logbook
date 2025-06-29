"use client"

import type React from "react"

import { useAuth } from "@/lib/contexts/auth-context"
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import { Button } from "@/components/ui/button"
import { Home, Dumbbell, History, Settings } from "lucide-react"
import { usePathname, useRouter } from "next/navigation"
import { cn } from "@/lib/utils"

interface AppShellProps {
  children: React.ReactNode
}

export function AppShell({ children }: AppShellProps) {
  const { user, logout } = useAuth()
  const pathname = usePathname()
  const router = useRouter()

  const navItems = [
    { icon: Home, label: "Home", path: "/" },
    { icon: Dumbbell, label: "Workout", path: "/workout" },
    { icon: History, label: "History", path: "/history" },
  ]

  return (
    <div className="min-h-screen bg-background text-foreground">
      {/* Header */}
      <header className="sticky top-0 z-50 h-14 border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
        <div className="flex h-14 items-center justify-between px-4">
          <div className="flex items-center gap-3">
            <Avatar className="h-8 w-8">
              <AvatarImage src={user?.profile_image_url || ""} alt={user?.name} />
              <AvatarFallback className="text-xs">
                {user?.name
                  ?.split(" ")
                  .map((n) => n[0])
                  .join("")
                  .toUpperCase()}
              </AvatarFallback>
            </Avatar>
            <span className="text-sm font-medium">{user?.name}</span>
          </div>
          <Button variant="ghost" size="icon" onClick={() => router.push("/settings")}>
            <Settings className="h-4 w-4" />
          </Button>
        </div>
      </header>

      {/* Main Content */}
      <main className="pb-18">{children}</main>

      {/* Bottom Navigation */}
      <nav className="fixed bottom-0 left-0 right-0 z-50 h-18 border-t bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
        <div className="flex h-18 items-center justify-around px-4">
          {navItems.map((item) => {
            const Icon = item.icon
            const isActive = pathname === item.path

            return (
              <Button
                key={item.path}
                variant="ghost"
                size="sm"
                className={cn(
                  "flex h-12 w-12 flex-col items-center justify-center gap-1 rounded-xl",
                  isActive && "bg-primary text-primary-foreground",
                )}
                onClick={() => router.push(item.path)}
              >
                <Icon className="h-5 w-5" />
                <span className="text-xs">{item.label}</span>
              </Button>
            )
          })}
        </div>
      </nav>
    </div>
  )
}
