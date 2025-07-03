"use client"

import { useSession, signOut } from "next-auth/react"

export default function ProfilePage() {
  const { data: session } = useSession()

  const handleSignOut = async () => {
    await signOut({ callbackUrl: "/" })
  }

  return (
    <div className="min-h-screen bg-gray-50 px-6 py-8">
      <h1 className="text-2xl font-bold mb-6">Profile</h1>

      <div className="bg-white rounded-lg p-6 mb-4">
        <div className="flex items-center gap-4 mb-4">
          <div className="w-16 h-16 bg-gray-200 rounded-full flex items-center justify-center">
            <span className="text-2xl font-semibold text-gray-600">
              {session?.user?.name?.[0]?.toUpperCase() || 'U'}
            </span>
          </div>
          <div>
            <h2 className="text-xl font-semibold">{session?.user?.name || "User"}</h2>
            <p className="text-gray-600">{session?.user?.email}</p>
          </div>
        </div>
      </div>

      <button
        onClick={handleSignOut}
        className="btn-secondary w-full"
      >
        Sign Out
      </button>
    </div>
  )
}
