interface Props {
  children: React.ReactNode
}

export default function ProtectedRoute({ children }: Props) {
  // Nginx auth_request 已做 SSO 鉴权，前端路由直接放行
  return <>{children}</>
}
