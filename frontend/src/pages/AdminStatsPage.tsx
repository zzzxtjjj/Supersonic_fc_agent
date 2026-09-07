import { useEffect, useState } from 'react'
import { AdminSeasonSelect } from '../components/admin/AdminSeasonSelect'
import { adminData } from '../services/adminData'
import type { AdminStatsPreview } from '../types/admin'

export function AdminStatsPage() {
  const [seasons, setSeasons] = useState<string[]>([])
  const [season, setSeason] = useState('')
  const [data, setData] = useState<AdminStatsPreview | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  useEffect(() => { adminData.getSeasons().then((items) => { setSeasons(items); setSeason(items.at(-1) ?? '') }).catch((e: unknown) => setError(e instanceof Error ? e.message : '赛季加载失败')) }, [])
  useEffect(() => { if (!season) return; setLoading(true); setError(null); adminData.getStatsPreview(season).then(setData).catch((e: unknown) => setError(e instanceof Error ? e.message : '统计加载失败')).finally(() => setLoading(false)) }, [season])
  return <section className="admin-page"><header className="admin-page-header with-control"><div><p className="section-kicker">DERIVED DATA</p><h1>统计预览</h1><p>只读查看由 Match Events 自动累计的进球和助攻。</p></div><AdminSeasonSelect seasons={seasons} value={season} onChange={setSeason} /></header>
    {loading ? <p className="admin-page-state">正在计算…</p> : error ? <p className="admin-error">{error}</p> : <div className="admin-two-column"><StatsList title="射手榜" rows={data?.scorers ?? []} field="goals" /><StatsList title="助攻榜" rows={data?.assists ?? []} field="assists" /></div>}
    <p className="admin-help-text">此页不提供编辑入口。要更正统计，请回到比赛页修改真实事件。</p>
  </section>
}

function StatsList({ title, rows, field }: { title: string; rows: AdminStatsPreview['scorers']; field: 'goals' | 'assists' }) {
  return <section className="admin-card admin-ranking"><h2>{title}</h2>{rows.length ? <ol>{rows.map((row) => <li key={row.playerId}><span>{row.name}<small>{row.playerId}</small></span><strong>{row[field] ?? 0}</strong></li>)}</ol> : <p className="admin-empty-inline">暂无已确认数据</p>}</section>
}
