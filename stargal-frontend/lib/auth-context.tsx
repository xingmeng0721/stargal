"use client"

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
} from "react"

interface AuthState {
  token: string | null
  isLoggedIn: boolean
  login: (token: string) => void
  logout: () => void
}

const AuthContext = createContext<AuthState>({
  token: null,
  isLoggedIn: false,
  login: () => {},
  logout: () => {},
})

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [token, setToken] = useState<string | null>(null)

  useEffect(() => {
    const stored = localStorage.getItem("access_token")
    if (stored) setToken(stored)
  }, [])

  // 监听 401 过期事件，自动清除登录态
  useEffect(() => {
    const handleExpired = () => {
      localStorage.removeItem("access_token")
      setToken(null)
    }
    window.addEventListener("auth:expired", handleExpired)
    return () => window.removeEventListener("auth:expired", handleExpired)
  }, [])

  const login = useCallback((newToken: string) => {
    localStorage.setItem("access_token", newToken)
    setToken(newToken)
  }, [])

  const logout = useCallback(() => {
    localStorage.removeItem("access_token")
    setToken(null)
  }, [])

  const value = useMemo(
    () => ({ token, isLoggedIn: !!token, login, logout }),
    [token, login, logout]
  )

  return <AuthContext value={value}>{children}</AuthContext>
}

export function useAuth() {
  return useContext(AuthContext)
}
