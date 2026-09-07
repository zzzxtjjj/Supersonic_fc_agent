import { useState, type ReactNode } from 'react'
import { NavLink } from 'react-router-dom'
import { usePlayerAuth } from '../../contexts/PlayerAuthContext'
import { PlayerAvatar } from '../players/PlayerAvatar'

const navItems = [
  { to: '/matches', label: '比赛' },
  { to: '/stats', label: '数据' },
  { to: '/ai', label: 'AI' },
  { to: '/gallery', label: '照片集' },
  { to: '/ratings', label: '评分' },
]

interface AppShellProps {
  children: ReactNode
}

export function AppShell({ children }: AppShellProps) {
  const [menuOpen, setMenuOpen] = useState(false)
  const { session, loading, logout } = usePlayerAuth()

  return (
    <div className="app-shell">
      <header className="site-header">
        <div className="header-inner">
          <NavLink className="brand" to="/ai" onClick={() => setMenuOpen(false)}>
            <span className="brand-logo-wrap">
              <img src="/supersonic-logo.png" alt="超音速球队队徽" />
            </span>
            <span>
              <strong>Supersonic FC</strong>
              <small>超音速</small>
            </span>
          </NavLink>

          <button
            className="menu-toggle"
            type="button"
            aria-label="切换导航"
            aria-expanded={menuOpen}
            onClick={() => setMenuOpen((open) => !open)}
          >
            <span />
            <span />
            <span />
          </button>

          <nav className={menuOpen ? 'site-nav is-open' : 'site-nav'}>
            {navItems.map((item) => (
              <NavLink
                key={item.to}
                to={item.to}
                onClick={() => setMenuOpen(false)}
                className={({ isActive }) => (isActive ? 'active' : undefined)}
              >
                {item.label}
              </NavLink>
            ))}
            {!loading && (session ? (
              <details className="player-nav-account">
                <summary><PlayerAvatar name={session.user.name} avatarUrl={session.user.photoUrl} size="tiny" /><span>{session.user.name}</span></summary>
                <div><strong>已认证超音速球员</strong><button type="button" onClick={() => logout()}>退出登录</button></div>
              </details>
            ) : (
              <NavLink className="player-login-nav" to="/player/login" onClick={() => setMenuOpen(false)}>球员登录</NavLink>
            ))}
          </nav>
        </div>
      </header>

      <main>{children}</main>

      <footer className="site-footer">
        <span>Supersonic FC</span>
        <div className="footer-meta">
          <span>为球队记忆，也为下一场比赛。</span>
          <NavLink className="admin-entry" to="/admin/login">
            管理
          </NavLink>
        </div>
      </footer>
    </div>
  )
}
