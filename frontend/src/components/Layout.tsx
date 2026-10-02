import { useEffect, useState } from 'react'
import { NavLink, Outlet } from 'react-router'
import { authApi } from '../api/auth'
import { useAuth } from '../auth/useAuth'

const NAV_ITEMS = [
  { to: '/', label: 'Dashboard', icon: '◎' },
  { to: '/health', label: 'Health', icon: '♥' },
  { to: '/money', label: 'Money', icon: '$' },
  { to: '/calendar', label: 'Calendar', icon: '▦' },
  { to: '/invest', label: 'Invest', icon: '↗' },
  { to: '/career', label: 'Career', icon: '★' },
]

// Sidebar + page area. Every page renders inside <Outlet />.
export function Layout() {
  const { authEnabled, logout } = useAuth()
  const [online, setOnline] = useState<boolean | null>(null)

  useEffect(() => {
    let active = true

    authApi
      .ready()
      .then(() => active && setOnline(true))
      .catch(() => active && setOnline(false))

    return () => {
      active = false
    }
  }, [])

  return (
    <div className="shell">
      <aside className="sidebar">
        <div className="brand">
          <h1>LifeOps</h1>
          <p>Your personal operating system.</p>
        </div>

        <nav className="nav">
          {NAV_ITEMS.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.to === '/'}
              className={({ isActive }) =>
                isActive ? 'nav-link active' : 'nav-link'
              }
            >
              <span className="nav-icon" aria-hidden="true">
                {item.icon}
              </span>
              {item.label}
            </NavLink>
          ))}
        </nav>

        <div className="sidebar-footer">
          <div className={online === false ? 'status offline' : 'status'}>
            <span className="status-dot" />
            {online === null
              ? 'Connecting…'
              : online
                ? 'System Online'
                : 'API Offline'}
          </div>

          {authEnabled && (
            <button className="secondary-button small" onClick={logout}>
              Log out
            </button>
          )}
        </div>
      </aside>

      <main className="dashboard">
        <Outlet />
      </main>
    </div>
  )
}
