import type { ReactNode } from 'react'
import { NavLink, useNavigate } from 'react-router-dom'
import { adminAuth } from '../../services/adminAuth'

const items = [
  { to: '/admin', label: '概览', end: true },
  { to: '/admin/media', label: '媒体' },
  { to: '/admin/seasons', label: '赛季' },
  { to: '/admin/players', label: '球员' },
  { to: '/admin/matches', label: '比赛' },
  { to: '/admin/stats', label: '统计预览' },
  { to: '/admin/invites', label: '球员邀请' },
]

export function AdminShell({ children }: { children: ReactNode }) {
  const navigate = useNavigate()
  async function logout() {
    await adminAuth.logout().catch(() => undefined)
    navigate('/admin/login', { replace: true })
  }
  return (
    <div className="admin-workspace">
      <aside className="admin-sidebar">
        <div><img src="/supersonic-logo.png" alt="超音速队徽" /><span><strong>Supersonic Admin</strong><small>球队数据管理</small></span></div>
        <nav>{items.map((item) => <NavLink key={item.to} to={item.to} end={item.end}>{item.label}</NavLink>)}</nav>
        <button type="button" onClick={logout}>退出管理</button>
      </aside>
      <div className="admin-main">{children}</div>
    </div>
  )
}
