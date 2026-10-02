import type { ReactNode } from 'react'
import { Navigate } from 'react-router'
import { useAuth } from '../auth/useAuth'

// Sends you to /login when auth is enabled and you have no token.
export function RequireAuth({ children }: { children: ReactNode }) {
  const { loading, isAuthenticated } = useAuth()

  if (loading) {
    return <p className="empty-state">Loading…</p>
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />
  }

  return <>{children}</>
}
