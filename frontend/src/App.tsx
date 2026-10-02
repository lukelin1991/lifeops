import { lazy, Suspense } from 'react'
import { BrowserRouter, Navigate, Route, Routes } from 'react-router'
import { AuthProvider } from './auth/AuthProvider'
import { Layout } from './components/Layout'
import { RequireAuth } from './components/RequireAuth'
import Login from './pages/Login'
import './App.css'
import './Layout.css'

// Each page is loaded on demand so the first download stays small
// (recharts in particular is fairly large).
const Dashboard = lazy(() => import('./pages/Dashboard'))
const Health = lazy(() => import('./pages/Health'))
const Money = lazy(() => import('./pages/Money'))
const Calendar = lazy(() => import('./pages/Calendar'))
const Invest = lazy(() => import('./pages/Invest'))
const Career = lazy(() => import('./pages/Career'))

function page(element: React.ReactNode) {
  return <Suspense fallback={<p className="muted">Loading...</p>}>{element}</Suspense>
}

function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<Login />} />

          <Route
            element={
              <RequireAuth>
                <Layout />
              </RequireAuth>
            }
          >
            <Route index element={page(<Dashboard />)} />
            <Route path="health" element={page(<Health />)} />
            <Route path="money" element={page(<Money />)} />
            <Route path="calendar" element={page(<Calendar />)} />
            <Route path="invest" element={page(<Invest />)} />
            <Route path="career" element={page(<Career />)} />
          </Route>

          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  )
}

export default App
