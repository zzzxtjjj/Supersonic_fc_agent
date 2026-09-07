import { useState, type FormEvent } from 'react'
import { Link } from 'react-router-dom'
import { playerAuth } from '../services/playerAuth'

export function PlayerActivatePage() {
  const [inviteCode, setInviteCode] = useState('')
  const [password, setPassword] = useState('')
  const [confirmation, setConfirmation] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [activated, setActivated] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function submit(event: FormEvent) {
    event.preventDefault()
    setError(null)
    if (password.length < 8) return setError('密码至少需要 8 个字符')
    if (password !== confirmation) return setError('两次输入的密码不一致')
    setSubmitting(true)
    try {
      await playerAuth.activate(inviteCode.trim(), password)
      setActivated(true)
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : '账号激活失败')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="page player-auth-page">
      <section className="player-auth-card">
        <img src="/supersonic-logo.png" alt="超音速球队队徽" />
        <p className="section-kicker">PLAYER ACTIVATION</p>
        <h1>激活球员账号</h1>
        {activated ? (
          <div className="activation-success"><strong>✓ 账号激活成功</strong><p>现在可以使用球员 ID 和新密码登录。</p><Link to="/player/login">前往登录</Link></div>
        ) : (
          <>
            <p>邀请码由球队管理员为已确认球员生成，网站不开放自由注册。</p>
            <form onSubmit={submit}>
              <label><span>邀请码</span><input autoComplete="one-time-code" value={inviteCode} onChange={(event) => setInviteCode(event.target.value)} required /></label>
              <label><span>设置密码</span><input type="password" autoComplete="new-password" minLength={8} value={password} onChange={(event) => setPassword(event.target.value)} required /></label>
              <label><span>确认密码</span><input type="password" autoComplete="new-password" minLength={8} value={confirmation} onChange={(event) => setConfirmation(event.target.value)} required /></label>
              {error && <p className="auth-error">{error}</p>}
              <button type="submit" disabled={submitting}>{submitting ? '激活中…' : '激活账号'}</button>
            </form>
            <div className="auth-links"><Link to="/player/login">已激活？前往登录</Link></div>
          </>
        )}
      </section>
    </div>
  )
}
