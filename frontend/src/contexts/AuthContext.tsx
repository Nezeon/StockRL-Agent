import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react'
import { authApi } from '../api/endpoints'
import type { User } from '../types/api'

interface AuthContextValue {
  user: User | null
  token: string | null
  login: (username: string, password: string) => Promise<void>
  register: (data: { username: string; email: string; password: string }) => Promise<void>
  logout: () => void
  isLoading: boolean
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [token, setToken] = useState<string | null>(null)
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    // Check if token exists in localStorage on mount
    const savedToken = localStorage.getItem('auth_token')
    if (savedToken) {
      setToken(savedToken)
      // Fetch user info
      authApi
        .getMe()
        .then((response) => {
          setUser(response.data)
        })
        .catch(() => {
          // Token invalid, remove it
          localStorage.removeItem('auth_token')
          setToken(null)
        })
        .finally(() => {
          setIsLoading(false)
        })
    } else {
      setIsLoading(false)
    }
  }, [])

  const login = async (username: string, password: string) => {
    const response = await authApi.login({ username, password })
    const { user: userData, access_token } = response.data

    localStorage.setItem('auth_token', access_token)
    setToken(access_token)
    setUser(userData)
  }

  const register = async (data: { username: string; email: string; password: string }) => {
    const response = await authApi.register(data)
    const { user: userData, access_token } = response.data

    localStorage.setItem('auth_token', access_token)
    setToken(access_token)
    setUser(userData)
  }

  const logout = () => {
    localStorage.removeItem('auth_token')
    setToken(null)
    setUser(null)
    window.location.href = '/login'
  }

  return (
    <AuthContext.Provider value={{ user, token, login, register, logout, isLoading }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}
