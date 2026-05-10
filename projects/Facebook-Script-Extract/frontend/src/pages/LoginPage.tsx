import { useEffect } from 'react'
import { useNavigate, useLocation } from 'react-router-dom'
import { login } from '../utils/auth'

export default function LoginPage() {
  const navigate = useNavigate()
  const location = useLocation()

  useEffect(() => {
    // Nginx auth_request 已确保用户通过 SSO 登录，直接创建前端 session 并跳转
    login('user', '')
    const from = (location.state as { from?: { pathname: string } } | null)?.from?.pathname || '/'
    navigate(from, { replace: true })
  }, [navigate, location])

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <p className="text-gray-500 text-sm">正在跳转...</p>
    </div>
  )
}
