import { RouteObject, Navigate } from 'react-router-dom'
import LoginPage from '../pages/login'
import MainLayout from '../layouts/MainLayout'
import DashboardPage from '../pages/dashboard'
import AccountListPage from '../pages/accounts'
import ContentCalendarPage from '../pages/contents'
import TopicListPage from '../pages/topics'
import SettingsPage from '../pages/settings'

function PrivateRoute({ children }: { children: React.ReactNode }) {
  const token = localStorage.getItem('access_token')
  return token ? children : <Navigate to="/login" replace />
}

export const routes: RouteObject[] = [
  {
    path: '/login',
    element: <LoginPage />,
  },
  {
    path: '/',
    element: (
      <PrivateRoute>
        <MainLayout />
      </PrivateRoute>
    ),
    children: [
      {
        index: true,
        element: <DashboardPage />,
      },
      {
        path: 'accounts',
        element: <AccountListPage />,
      },
      {
        path: 'contents',
        element: <ContentCalendarPage />,
      },
      {
        path: 'topics',
        element: <TopicListPage />,
      },
      {
        path: 'settings',
        element: <SettingsPage />,
      },
    ],
  },
]
