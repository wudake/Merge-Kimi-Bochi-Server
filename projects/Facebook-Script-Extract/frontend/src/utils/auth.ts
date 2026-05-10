const AUTH_KEY = 'fbse_auth_session'
const SESSION_DAYS = 7

interface Session {
  user: string
  expiry: number
}

function readSession(): Session | null {
  const raw = localStorage.getItem(AUTH_KEY)
  if (!raw) return null
  try {
    const session = JSON.parse(raw) as Session
    if (Date.now() > session.expiry) {
      localStorage.removeItem(AUTH_KEY)
      return null
    }
    return session
  } catch {
    localStorage.removeItem(AUTH_KEY)
    return null
  }
}

export function login(username: string, _password: string): boolean {
  // Nginx auth_request 已做 SSO 鉴权，前端不再验证密码
  const session: Session = {
    user: username || 'user',
    expiry: Date.now() + SESSION_DAYS * 24 * 60 * 60 * 1000,
  }
  localStorage.setItem(AUTH_KEY, JSON.stringify(session))
  return true
}

export function logout(): void {
  localStorage.removeItem(AUTH_KEY)
  // 同时调用 OPMan 的 logout 以清除 SSO Cookie
  fetch('/op/api/v1/auth/logout', { method: 'POST', credentials: 'include' })
    .catch(() => {})
}

export function isAuthenticated(): boolean {
  // Nginx auth_request 已确保只有登录用户能访问本应用
  return true
}

export function getCurrentUser(): string | null {
  return readSession()?.user ?? null
}

export function isAuthConfigured(): boolean {
  return true
}
