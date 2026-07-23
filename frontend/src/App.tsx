import React, { useEffect } from 'react'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { Provider } from 'react-redux'
import { store } from './store'
import { useAppDispatch, useAppSelector } from './hooks/reduxHooks'
import { fetchCurrentUser } from './store/authSlice'
import Login from './pages/Login'
import Dashboard from './pages/Dashboard'

// ---- Auth guard ----
function PrivateRoute({ children }: { children: React.ReactNode }) {
  const { accessToken, isLoading } = useAppSelector((s) => s.auth)
  if (isLoading) return null
  if (!accessToken) return <Navigate to="/login" replace />
  return <>{children}</>
}

// ---- App initialiser — fetch current user on mount if token exists ----
function AppInit() {
  const dispatch = useAppDispatch()
  const { accessToken } = useAppSelector((s) => s.auth)

  useEffect(() => {
    if (accessToken) dispatch(fetchCurrentUser())
  }, [])

  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route
        path="/dashboard"
        element={
          <PrivateRoute>
            <Dashboard />
          </PrivateRoute>
        }
      />
      {/* Default redirect */}
      <Route path="/" element={<Navigate to="/dashboard" replace />} />
      <Route path="*" element={<Navigate to="/dashboard" replace />} />
    </Routes>
  )
}

export default function App() {
  return (
    <Provider store={store}>
      <BrowserRouter>
        <AppInit />
      </BrowserRouter>
    </Provider>
  )
}
