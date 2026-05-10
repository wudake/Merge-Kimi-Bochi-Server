import { Link, Outlet, useLocation } from 'react-router-dom'
import { ClipboardList, PlayCircle, Settings, Video, FileText, LogOut, UserCircle2 } from 'lucide-react'
import { logout, getCurrentUser } from '../utils/auth'

const navItems = [
  { path: '/', label: '新建任务', icon: PlayCircle },
  { path: '/tasks', label: '任务列表', icon: ClipboardList },
  { path: '/completed', label: '已完成视频脚本', icon: FileText },
  { path: '/settings', label: '设置', icon: Settings },
]

export default function Layout() {
  const location = useLocation()
  const user = getCurrentUser()

  const handleLogout = () => {
    logout()
    // 强制整页跳转，让 Nginx auth_request 重新鉴权（未登录则跳转到 OP 登录页）
    window.location.href = '/fbse/login'
  }

  return (
    <div className="min-h-screen flex flex-col">
      <header className="bg-white border-b border-gray-200 sticky top-0 z-50">
        <div className="max-w-6xl mx-auto px-4 h-14 flex items-center justify-between">
          <Link to="/" className="flex items-center gap-2 text-primary-700 font-bold text-lg">
            <Video className="w-6 h-6" />
            <span>Video Script Extractor</span>
          </Link>
          <nav className="flex items-center gap-1">
            {navItems.map((item) => {
              const active = location.pathname === item.path ||
                (item.path !== '/' && location.pathname.startsWith(item.path))
              const Icon = item.icon
              return (
                <Link
                  key={item.path}
                  to={item.path}
                  className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md text-sm font-medium transition-colors ${
                    active
                      ? 'bg-primary-50 text-primary-700'
                      : 'text-gray-600 hover:bg-gray-100 hover:text-gray-900'
                  }`}
                >
                  <Icon className="w-4 h-4" />
                  {item.label}
                </Link>
              )
            })}
            <div className="ml-2 pl-2 border-l border-gray-200 flex items-center gap-2">
              {user && (
                <span className="hidden sm:flex items-center gap-1 text-xs text-gray-500">
                  <UserCircle2 className="w-4 h-4" />
                  {user}
                </span>
              )}
              <button
                onClick={handleLogout}
                title="退出登录"
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-md text-sm font-medium text-gray-600 hover:bg-red-50 hover:text-red-600 transition-colors"
              >
                <LogOut className="w-4 h-4" />
                <span className="hidden sm:inline">退出</span>
              </button>
            </div>
          </nav>
        </div>
      </header>

      <main className="flex-1 max-w-6xl w-full mx-auto px-4 py-6">
        <Outlet />
      </main>

      <footer className="bg-white border-t border-gray-200 py-4">
        <div className="max-w-6xl mx-auto px-4 text-center text-xs text-gray-400">
          Video Script Extractor - Team Edition
        </div>
      </footer>
    </div>
  )
}
