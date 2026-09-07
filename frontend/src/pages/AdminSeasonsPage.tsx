import { useEffect, useState, type FormEvent } from 'react'
import { adminData } from '../services/adminData'

interface TeamDraft { id: string; name: string; crestUrl: string }

export function AdminSeasonsPage() {
  const [seasons, setSeasons] = useState<string[]>([])
  const [seasonId, setSeasonId] = useState('')
  const [teams, setTeams] = useState<TeamDraft[]>([])
  const [saving, setSaving] = useState(false)
  const [notice, setNotice] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)
  const load = () => adminData.getSeasons().then(setSeasons).catch((e: unknown) => setError(e instanceof Error ? e.message : '赛季加载失败'))
  useEffect(() => { load() }, [])

  async function submit(event: FormEvent) {
    event.preventDefault(); setSaving(true); setNotice(null); setError(null)
    try {
      await adminData.createSeason(
        seasonId,
        teams.filter((team) => team.id && team.name).map((team) => ({
          id: team.id.trim(),
          name: team.name.trim(),
          crest_url: team.crestUrl.trim() || null,
          aliases: [],
        })),
      )
      setNotice(`赛季 ${seasonId} 已创建。`); setSeasonId(''); setTeams([]); await load()
    } catch (e) { setError(e instanceof Error ? e.message : '赛季创建失败') } finally { setSaving(false) }
  }

  return <section className="admin-page"><header className="admin-page-header"><p className="section-kicker">SEASONS</p><h1>赛季管理</h1><p>创建与现有 data/seasons 格式一致的新赛季，不会自动编造球队。</p></header>
    <div className="admin-two-column"><section className="admin-card"><h2>已有赛季</h2>{seasons.length ? <div className="season-admin-list">{seasons.map((season) => <strong key={season}>{season}</strong>)}</div> : <p className="admin-empty-inline">暂无赛季</p>}</section>
    <form className="admin-card admin-form" onSubmit={submit}><h2>+新建赛季</h2><label><span>Season ID（XX-XX）</span><input pattern="\d{2}-\d{2}" placeholder="27-28" value={seasonId} onChange={(e) => setSeasonId(e.target.value)} required /></label><div className="admin-section-title"><strong>初始球队（可选）</strong><button type="button" onClick={() => setTeams((items) => [...items, { id: '', name: '', crestUrl: '' }])}>+添加球队</button></div>{teams.map((team, index) => <div className="team-draft-row" key={index}><input placeholder="team-id" value={team.id} onChange={(e) => setTeams((items) => items.map((item, current) => current === index ? { ...item, id: e.target.value } : item))} /><input placeholder="球队名称" value={team.name} onChange={(e) => setTeams((items) => items.map((item, current) => current === index ? { ...item, name: e.target.value } : item))} /><input placeholder="crest_url（可选）" value={team.crestUrl} onChange={(e) => setTeams((items) => items.map((item, current) => current === index ? { ...item, crestUrl: e.target.value } : item))} /><button type="button" onClick={() => setTeams((items) => items.filter((_, current) => current !== index))}>删除</button></div>)}<button className="admin-primary" type="submit" disabled={saving}>{saving ? '创建中…' : '创建赛季'}</button>{notice && <p className="admin-success">{notice}</p>}{error && <p className="admin-error">{error}</p>}</form></div>
  </section>
}
