import React from 'react'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { AuthProvider } from './contexts/AuthContext'
import { PrivateRoute } from './components/PrivateRoute'
import { Login } from './pages/Login'
import { Register } from './pages/Register'
import { Dashboard } from './pages/Dashboard'
import { PortfolioSettings } from './pages/PortfolioSettings'
import { TradeLog } from './pages/TradeLog'
import { AgentMonitor } from './pages/AgentMonitor'

function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />
          <Route
            path="/"
            element={
              <PrivateRoute>
                <Dashboard />
              </PrivateRoute>
            }
          />
          <Route
            path="/portfolio/settings"
            element={
              <PrivateRoute>
                <PortfolioSettings />
              </PrivateRoute>
            }
          />
          <Route
            path="/trades"
            element={
              <PrivateRoute>
                <TradeLog />
              </PrivateRoute>
            }
          />
          <Route
            path="/agent/:runId"
            element={
              <PrivateRoute>
                <AgentMonitor />
              </PrivateRoute>
            }
          />
          <Route path="*" element={<Navigate to="/" />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  )
}

export default App
