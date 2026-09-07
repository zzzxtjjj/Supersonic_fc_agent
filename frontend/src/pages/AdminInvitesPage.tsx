import { useEffect, useState } from 'react'
import { AdminSeasonSelect } from '../components/admin/AdminSeasonSelect'
import { adminData } from '../services/adminData'
import type { AdminPlayer } from '../types/admin'

export function AdminInvitesPage() {
  const [seasons, setSeasons] = useState<string[]>([])
  const [season, setSeason] = useState('')
  const [players, setPlayers] = useState<AdminPlayer[]>([])
  const [playerId, setPlayerId] = useState('')
  const [result, setResult] = useState<{ code: string; expiresAt: string } | null>(null)
  const [loading, setLoading] = useState(true)
  const [generating, setGenerating] = useState(false)
  const [notice, setNotice] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    adminData.getSeasons().then((items) => { setSeasons(items); setSeason(items.at(-1) ?? '') }).catch((e: unknown) => setError(e instanceof Error ? e.message : '赛季加载失败')).finally(() => setLoading(false))
  }, [])
  useEffect(() => {
    if (!season) return
    setResult(null)
    adminData.getPlayers(season).then((items) => { setPlayers(items); setPlayerId(items[0]?.id ?? '') }).catch((e: unknown) => setError(e instanceof Error ? e.message : '球员加载失败'))
  }, [season])

  async function generate() {
    if (!playerId) return
    setGenerating(true); setError(null); setNotice(null); setResult(null)
    try {
      const response = await adminData.createInvite(playerId)
      setResult({ code: response.invite_code, expiresAt: response.expires_at })
    } catch (e) { setError(e instanceof Error ? e.message : '邀请码生成失败') } finally { setGenerating(false) }
  }

  async function copy() {
    if (!result) return
    await navigator.clipboard.writeText(result.code)
    setNotice('邀请码已复制。')
  }

  return <section className="admin-page"><header className="admin-page-header"><p className="section-kicker">PLAYER ACCESS</p><h1>球员邀请</h1><p>只为官方名单中的球员生成一次性激活码。</p></header>
    <div className="admin-card admin-compact-form">
      {loading ? <p>正在加载…</p> : <><AdminSeasonSelect seasons={seasons} value={season} onChange={setSeason} /><label><span>Player</span><select value={playerId} onChange={(e) => { setPlayerId(e.target.value); setResult(null) }}><option value="">选择球员</option>{players.map((player) => <option key={player.id} value={player.id}>{player.name} · #{player.season_data?.number ?? '—'}</option>)}</select></label><button className="admin-primary" type="button" disabled={!playerId || generating} onClick={generate}>{generating ? '生成中…' : '生成邀请码'}</button></>}
      {result && <div className="invite-result"><span>一次性邀请码</span><strong>{result.code}</strong><small>有效期至：{new Date(result.expiresAt).toLocaleString('zh-CN')}</small><button type="button" onClick={copy}>复制邀请码</button><p>此邀请码只在这里显示一次，请发送给对应球员。</p></div>}
      {notice && <p className="admin-success">{notice}</p>}{error && <p className="admin-error">{error}</p>}
    </div>
  </section>
}
