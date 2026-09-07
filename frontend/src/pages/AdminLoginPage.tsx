import { useEffect, useState, type FormEvent } from 'react'
import { Link, Navigate, useLocation, useNavigate } from 'react-router-dom'
import { adminAuth } from '../services/adminAuth'


export function AdminLoginPage() {
  const navigate = useNavigate()
  const location = useLocation()
  const [checking, setChecking] = useState(true)
  const [authenticated, setAuthenticated] = useState(false)
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const controller = new AbortController()
    adminAuth
      .getSession(controller.signal)
      .then((result) => setAuthenticated(result.authenticated))
      .catch(() => setAuthenticated(false))
      .finally(() => setChecking(false))
    return () => controller.abort()
  }, [])

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setSubmitting(true)
    setError(null)
    try {
      await adminAuth.login(username, password)
      const destination = (
        location.state as { from?: string } | null
      )?.from ?? '/admin'
      navigate(destination, { replace: true })
    } catch (loginError) {
      setError(
        loginError instanceof Error
          ? loginError.message
          : '管理员登录失败',
      )
    } finally {
      setSubmitting(false)
    }
  }

  if (!checking && authenticated) {
    return <Navigate to="/admin" replace />
  }

  return (
    <div className="page admin-login-page">
      <section className="admin-login-card">
        <img src="/supersonic-logo.png" alt="超音速球队队徽" />
        <p className="section-kicker">PRIVATE ADMIN</p>
        <h1>管理员登录</h1>
        <p>用于球队数据、比赛事件与媒体管理。网站没有公开注册。</p>

        <form onSubmit={submit}>
          <label>
            <span>管理员账号</span>
            <input
              autoComplete="username"
              value={username}
              onChange={(event) => setUsername(event.target.value)}
              required
            />
          </label>
          <label>
            <span>密码</span>
            <input
              type="password"
              autoComplete="current-password"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              required
            />
          </label>
          {error && <p className="admin-login-error">{error}</p>}
          <button type="submit" disabled={checking || submitting}>
            {submitting ? '正在登录…' : '登录'}
          </button>
        </form>

        <Link className="admin-back-link" to="/ai">
          返回公开网站
        </Link>
      </section>
    </div>
  )
}
