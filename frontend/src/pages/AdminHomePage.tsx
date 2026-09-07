import { Link } from 'react-router-dom'

const cards = [
  { to: '/admin/matches', title: '比赛与事件', text: '录入比分、进球、助攻、队长和门将。' },
  { to: '/admin/players', title: '球员资料', text: '维护号码、位置、头像、转会与里程碑。' },
  { to: '/admin/invites', title: '球员邀请', text: '为已确认球员生成一次性账号邀请码。' },
  { to: '/admin/media', title: '媒体与头像', text: '上传球员照片、合照和球队队徽。' },
  { to: '/admin/seasons', title: '赛季', text: '创建新赛季及其初始球队。' },
  { to: '/admin/stats', title: '统计预览', text: '从比赛事件只读查看进球和助攻累计。' },
]

export function AdminHomePage() {
  return <section className="admin-page"><header className="admin-page-header"><p className="section-kicker">CONTROL ROOM</p><h1>管理后台</h1><p>日常维护球队官方数据与社区访问权限。</p></header><div className="admin-dashboard-grid">{cards.map((card) => <Link key={card.to} to={card.to}><strong>{card.title}</strong><p>{card.text}</p><span>进入 →</span></Link>)}</div></section>
}
