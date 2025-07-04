"use client"

import { usePathname, useRouter } from 'next/navigation'
import { User, Dumbbell, ListChecks } from 'lucide-react'
import { cn } from '@/lib/utils'

const navItems = [
  {
    icon: User,
    label: 'Profile',
    path: '/profile',
  },
  {
    icon: Dumbbell,
    label: 'Workouts',
    path: '/',
  },
  {
    icon: ListChecks,
    label: 'Exercises',
    path: '/exercises',
  },
]

export function BottomNav() {
  const pathname = usePathname()
  const router = useRouter()

  return (
    <nav className="fixed bottom-0 left-0 right-0 bg-white border-t border-gray-200">
      <div className="flex justify-around items-center h-16 max-w-lg mx-auto">
        {navItems.map((item) => {
          const isActive = pathname === item.path ||
            (item.path === '/' && pathname.startsWith('/workout'))
          const Icon = item.icon

          return (
            <button
              key={item.path}
              onClick={() => router.push(item.path)}
              className={cn(
                "flex flex-col items-center justify-center flex-1 h-full px-2 py-2",
                "text-xs font-medium transition-colors",
                isActive
                  ? "text-black"
                  : "text-gray-400 hover:text-gray-600"
              )}
            >
              <Icon className={cn(
                "w-6 h-6 mb-1",
                isActive && "stroke-[2.5]"
              )} />
              <span>{item.label}</span>
            </button>
          )
        })}
      </div>
    </nav>
  )
}
