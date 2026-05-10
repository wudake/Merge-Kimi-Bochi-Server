import { create } from 'zustand'

interface UserInfo {
  id: string
  username: string
  realName: string
  role: string
  avatar: string | null
}

interface AuthState {
  token: string | null
  refreshToken: string | null
  user: UserInfo | null
  isAuthenticated: boolean
  setAuth: (token: string, refreshToken: string, user: UserInfo) => void
  clearAuth: () => void
  setUser: (user: UserInfo) => void
}

export const useAuthStore = create<AuthState>((set) => ({
  token: localStorage.getItem('access_token'),
  refreshToken: localStorage.getItem('refresh_token'),
  user: (() => {
    try {
      const raw = localStorage.getItem('user')
      return raw ? JSON.parse(raw) : null
    } catch {
      return null
    }
  })(),
  isAuthenticated: !!localStorage.getItem('access_token'),
  setAuth: (token, refreshToken, user) => {
    localStorage.setItem('access_token', token)
    localStorage.setItem('refresh_token', refreshToken)
    localStorage.setItem('user', JSON.stringify(user))
    set({ token, refreshToken, user, isAuthenticated: true })
  },
  clearAuth: () => {
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
    localStorage.removeItem('user')
    set({ token: null, refreshToken: null, user: null, isAuthenticated: false })
  },
  setUser: (user) => set({ user }),
}))
