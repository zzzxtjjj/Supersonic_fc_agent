import { useState, type FormEvent } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'
import { usePlayerAuth } from '../contexts/PlayerAuthContext'
import { playerAuth } from '../services/playerAuth'

export function PlayerLoginPage() {
  const navigate = useNavigate()
  const location = useLocation()
  const { refresh } = usePlayerAuth()
  const [playerId, setPlayerId] = useState('')
  const [password, setPassword] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function submit(event: FormEvent) {
    event.preventDefault()
    setSubmitting(true)
    setError(null)
    try {
      await playerAuth.login(playerId.trim(), password)
      await refresh()
      const destination = (location.state as { from?: string } | null)?.from ?? '/ratings'
      navigate(destination, { replace: true })
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : '登录失败')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="page player-auth-page">
      <section className="player-auth-card">
        <img src="/supersonic-logo.png" alt="超音速球队队徽" />
        <p className="section-kicker">PLAYER ACCESS</p>
        <h1>球员登录</h1>
        <p>使用管理员邀请激活的球员账号参与比赛评分与球队讨论。</p>
        <form onSubmit={submit}>
          <label><span>球员 ID</span><input autoComplete="username" value={playerId} onChange={(event) => setPlayerId(event.target.value)} required /></label>
          <label><span>密码</span><input type="password" autoComplete="current-password" value={password} onChange={(event) => setPassword(event.target.value)} required /></label>
          {error && <p className="auth-error">{error}</p>}
          <button type="submit" disabled={submitting}>{submitting ? '登录中…' : '登录'}</button>
        </form>
        <div className="auth-links"><Link to="/player/activate">有邀请码？先激活账号</Link><Link to="/ratings">返回评分</Link></div>
      </section>
    </div>
  )
}
