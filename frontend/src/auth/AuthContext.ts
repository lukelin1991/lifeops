import { createContext } from 'react'

export type AuthState = {
  // Still asking the API whether auth is enabled
  loading: boolean
  // Could not reach the API at all
  offline: boolean
  authEnabled: boolean
  isAuthenticated: boolean
  login: (username: string, password: string) => Promise<void>
  logout: () => void
}

export const AuthContext = createContext<AuthState | null>(null)
