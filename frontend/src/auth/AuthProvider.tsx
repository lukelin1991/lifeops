import { useCallback, useEffect, useMemo, useState } from 'react'
import type { ReactNode } from 'react'
import { authApi } from '../api/auth'
import { getToken, setToken, UNAUTHORIZED_EVENT } from '../api/client'
import { AuthContext } from './AuthContext'

// Asks the API whether login is required (GET /auth/config).
// With AUTH_ENABLED=false (local default) the app works without a login,
// exactly like the original single-page version.
export function AuthProvider({ children }: { children: ReactNode }) {
  const [loading, setLoading] = useState(true)
  const [offline, setOffline] = useState(false)
  const [authEnabled, setAuthEnabled] = useState(false)
  const [token, setTokenState] = useState<string | null>(getToken())

  useEffect(() => {
    let active = true

    authApi
      .config()
      .then((config) => {
        if (!active) return
        setAuthEnabled(config.auth_enabled)
        setOffline(false)
      })
      .catch(() => {
        if (active) setOffline(true)
      })
      .finally(() => {
        if (active) setLoading(false)
      })

    return () => {
      active = false
    }
  }, [])

  // The API client fires this when a request comes back 401.
  useEffect(() => {
    const onUnauthorized = () => setTokenState(null)
    window.addEventListener(UNAUTHORIZED_EVENT, onUnauthorized)
    return () =>
      window.removeEventListener(UNAUTHORIZED_EVENT, onUnauthorized)
  }, [])

  const login = useCallback(async (username: string, password: string) => {
    const result = await authApi.login(username, password)
    setToken(result.access_token)
    setTokenState(result.access_token)
  }, [])

  const logout = useCallback(() => {
    setToken(null)
    setTokenState(null)
  }, [])

  const value = useMemo(
    () => ({
      loading,
      offline,
      authEnabled,
      isAuthenticated: !authEnabled || token !== null,
      login,
      logout,
    }),
    [loading, offline, authEnabled, token, login, logout],
  )

  return (
    <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
  )
}
