import request from './request'

export interface LoginParams {
  username: string
  password: string
}

export interface LoginResult {
  accessToken: string
  refreshToken: string
  user: {
    id: string
    username: string
    realName: string
    role: string
    avatar: string | null
  }
}

export const login = (params: LoginParams): Promise<LoginResult> =>
  request.post('/auth/login', params)

export const logout = (): Promise<void> => request.post('/auth/logout')

export const refreshToken = (refreshToken: string): Promise<{ accessToken: string }> =>
  request.post('/auth/refresh', { refreshToken })

export const getCurrentUser = (): Promise<LoginResult['user']> =>
  request.get('/auth/me')
