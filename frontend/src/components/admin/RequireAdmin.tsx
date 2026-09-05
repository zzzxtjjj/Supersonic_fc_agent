import { useEffect, useState, type ReactNode } from 'react'
import { Navigate, useLocation } from 'react-router-dom'
import { adminAuth } from '../../services/adminAuth'


export function RequireAdmin({ children }: { children: ReactNode }) {
  const location = useLocation()
  const [authenticated, setAuthenticated] = useState<boolean | null>(null)

  useEffect(() => {
    const controller = new AbortController()
    adminAuth
      .getSession(controller.signal)
      .then((result) => setAuthenticated(result.authenticated))
      .catch(() => setAuthenticated(false))
    return () => controller.abort()
  }, [])

  if (authenticated === null) {
    return <div className="admin-auth-loading">正在验证管理员身份…</div>
  }

  if (!authenticated) {
    return <Navigate to="/admin/login" replace state={{ from: location.pathname }} />
  }

  return children
}
