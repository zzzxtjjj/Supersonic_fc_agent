import { useEffect, useMemo, useState, type FormEvent } from 'react'
import { AdminSeasonSelect } from '../components/admin/AdminSeasonSelect'
import { PlayerAvatar } from '../components/players/PlayerAvatar'
import { adminData } from '../services/adminData'
import type { AdminPlayer } from '../types/admin'

interface PlayerForm {
  id: string
  name: string
  aliases: string
  photoUrl: string
  number: string
  position: string
  departureReason: string
  departureAfterSeason: string
  destination: string
  destinationDetail: string
  transfers: Record<string, unknown>[]
  milestones: Record<string, unknown>[]
}

const emptyForm = (): PlayerForm => ({
  id: '', name: '', aliases: '', photoUrl: '', number: '', position: '',
  departureReason: '', departureAfterSeason: '', destination: '', destinationDetail: '',
  transfers: [], milestones: [],
})

function playerToForm(player: AdminPlayer): PlayerForm {
  const departure = player.departure ?? {}
  const text = (value: unknown) => typeof value === 'string' ? value : ''
  return {
    id: player.id,
    name: player.name,
    aliases: player.aliases?.join('\uff0c') ?? '',
    photoUrl: player.photo_url ?? '',
    number: player.season_data?.number == null ? '' : String(player.season_data.number),
    position: text(player.season_data?.position),
    departureReason: text(departure.reason),
    departureAfterSeason: text(departure.after_season),
    destination: text(departure.destination),
    destinationDetail: text(departure.destination_detail),
    transfers: player.transfers?.map((item) => ({ ...item })) ?? [],
    milestones: player.career_milestones?.map((item) => ({ ...item })) ?? [],
  }
}

export function AdminPlayersPage() {
  const [seasons, setSeasons] = useState<string[]>([])
  const [season, setSeason] = useState('')
  const [players, setPlayers] = useState<AdminPlayer[]>([])
  const [selectedId, setSelectedId] = useState<string | null>(null)
  const [form, setForm] = useState<PlayerForm>(emptyForm)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [notice, setNotice] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)
  const selected = useMemo(() => players.find((player) => player.id === selectedId) ?? null, [players, selectedId])

  useEffect(() => {
    adminData.getSeasons().then((items) => {
      setSeasons(items)
      setSeason(items.at(-1) ?? '')
    }).catch((reason: unknown) => setError(reason instanceof Error ? reason.message : '\u8d5b\u5b63\u52a0\u8f7d\u5931\u8d25'))
  }, [])

  useEffect(() => {
    if (!season) { setLoading(false); return }
    const controller = new AbortController()
    setLoading(true); setError(null); setNotice(null); setSelectedId(null); setForm(emptyForm())
    adminData.getPlayers(season, controller.signal).then(setPlayers).catch((reason: unknown) => {
      if (!controller.signal.aborted) setError(reason instanceof Error ? reason.message : '\u7403\u5458\u52a0\u8f7d\u5931\u8d25')
    }).finally(() => { if (!controller.signal.aborted) setLoading(false) })
    return () => controller.abort()
  }, [season])

  function edit(player: AdminPlayer) {
    setSelectedId(player.id); setForm(playerToForm(player)); setNotice(null); setError(null)
  }
  function createNew() { setSelectedId(null); setForm(emptyForm()); setNotice(null); setError(null) }
  function field<K extends keyof PlayerForm>(key: K, value: PlayerForm[K]) { setForm((current) => ({ ...current, [key]: value })) }
  function rowField(kind: 'transfers' | 'milestones', index: number, key: string, value: string) {
    setForm((current) => ({ ...current, [kind]: current[kind].map((row, currentIndex) => currentIndex === index ? { ...row, [key]: value || null } : row) }))
  }

  async function save(event: FormEvent) {
    event.preventDefault(); setSaving(true); setError(null); setNotice(null)
    const aliases = form.aliases.split(/[,\uff0c]/).map((item) => item.trim()).filter(Boolean)
    const seasonData = { ...(selected?.season_data ?? {}), number: form.number ? Number(form.number) : null, position: form.position.trim() || null }
    const departure = form.departureReason || form.departureAfterSeason || form.destination || form.destinationDetail ? {
      reason: form.departureReason || null,
      after_season: form.departureAfterSeason || null,
      destination: form.destination || null,
      destination_detail: form.destinationDetail || null,
    } : null
    const transfers = form.transfers.length ? form.transfers : null
    const careerMilestones = form.milestones.length ? form.milestones : null
    try {
      let saved: AdminPlayer
      if (selected) {
        saved = await adminData.updatePlayer(season, selected.id, {
          name: form.name.trim(), aliases, photo_url: form.photoUrl.trim() || null,
          season_data: seasonData, departure, transfers, career_milestones: careerMilestones,
        })
        setPlayers((items) => items.map((item) => item.id === saved.id ? saved : item))
      } else {
        saved = await adminData.createPlayer(season, {
          id: form.id.trim(), name: form.name.trim(), aliases,
          photo_url: form.photoUrl.trim() || null, season_data: seasonData,
          ...(departure ? { departure } : {}),
          ...(transfers ? { transfers } : {}),
          ...(careerMilestones ? { career_milestones: careerMilestones } : {}),
        })
        setPlayers((items) => [...items, saved]); setSelectedId(saved.id); setForm(playerToForm(saved))
      }
      setNotice(`\u7403\u5458 ${saved.name} \u5df2\u4fdd\u5b58\u3002`)
    } catch (reason) { setError(reason instanceof Error ? reason.message : '\u7403\u5458\u4fdd\u5b58\u5931\u8d25') } finally { setSaving(false) }
  }

  return <section className="admin-page">
    <header className="admin-page-header with-control"><div><p className="section-kicker">ROSTER</p><h1>\u7403\u5458\u8d44\u6599</h1><p>\u7ef4\u62a4\u5df2\u786e\u8ba4\u8d44\u6599\uff1b\u7559\u7a7a\u8868\u793a\u5f85\u8865\u5145\uff0c\u4e0d\u4f1a\u81ea\u52a8\u731c\u6d4b\u3002</p></div><AdminSeasonSelect seasons={seasons} value={season} onChange={setSeason} /></header>
    <div className="admin-editor-layout">
      <section className="admin-card admin-record-list"><div className="admin-section-title"><h2>\u540d\u5355 <small>{players.length}</small></h2><button type="button" onClick={createNew}>+ \u65b0\u589e\u7403\u5458</button></div>{loading ? <p>\u6b63\u5728\u52a0\u8f7d\u2026</p> : players.length ? players.map((player) => <button className={selectedId === player.id ? 'selected' : ''} type="button" key={player.id} onClick={() => edit(player)}><PlayerAvatar name={player.name} avatarUrl={player.photo_url ?? null} size="small" /><span><strong>{player.name}</strong><small>#{player.season_data?.number ?? '\u2014'} \u00b7 {String(player.season_data?.position ?? '\u8d44\u6599\u5f85\u8865\u5145')}</small></span></button>) : <p className="admin-empty-inline">\u8be5\u8d5b\u5b63\u6682\u65e0\u7403\u5458</p>}</section>
      <form className="admin-card admin-form admin-player-form" onSubmit={save}><div className="admin-section-title"><h2>{selected ? `\u7f16\u8f91 ${selected.name}` : '\u65b0\u589e\u7403\u5458'}</h2>{selected && <button type="button" onClick={createNew}>\u53d6\u6d88\u7f16\u8f91</button>}</div>
        <div className="admin-form-grid"><label><span>Player ID</span><input value={form.id} disabled={Boolean(selected)} pattern="[a-z0-9][a-z0-9-]*" onChange={(e) => field('id', e.target.value)} required /></label><label><span>\u59d3\u540d</span><input value={form.name} onChange={(e) => field('name', e.target.value)} required /></label><label><span>\u53f7\u7801</span><input type="number" min="0" value={form.number} onChange={(e) => field('number', e.target.value)} /></label><label><span>\u4f4d\u7f6e</span><input value={form.position} onChange={(e) => field('position', e.target.value)} /></label><label className="wide-field"><span>\u522b\u540d\uff08\u9017\u53f7\u5206\u9694\uff09</span><input value={form.aliases} onChange={(e) => field('aliases', e.target.value)} /></label><label className="wide-field"><span>photo_url</span><input placeholder="/media/player/..." value={form.photoUrl} onChange={(e) => field('photoUrl', e.target.value)} /></label></div>
        <details><summary>\u79bb\u961f\u8d44\u6599\uff08\u53ef\u9009\uff09</summary><div className="admin-form-grid"><label><span>\u539f\u56e0</span><input value={form.departureReason} onChange={(e) => field('departureReason', e.target.value)} /></label><label><span>\u8d5b\u5b63\u540e</span><input value={form.departureAfterSeason} onChange={(e) => field('departureAfterSeason', e.target.value)} /></label><label><span>\u53bb\u5411</span><input value={form.destination} onChange={(e) => field('destination', e.target.value)} /></label><label><span>\u53bb\u5411\u8be6\u60c5</span><input value={form.destinationDetail} onChange={(e) => field('destinationDetail', e.target.value)} /></label></div></details>
        <details><summary>\u8f6c\u4f1a\u8bb0\u5f55\uff08\u53ef\u9009\uff09</summary><div className="admin-repeat-list">{form.transfers.map((row, index) => <div className="admin-repeat-row" key={index}><div className="admin-form-grid"><label><span>\u7c7b\u578b</span><select value={String(row.type ?? '')} onChange={(e) => rowField('transfers', index, 'type', e.target.value)}><option value="">\u672a\u586b\u5199</option><option value="transfer_in">\u8f6c\u5165</option><option value="transfer_out">\u8f6c\u51fa</option></select></label><label><span>\u65f6\u70b9</span><input placeholder="mid-season" value={String(row.timing ?? '')} onChange={(e) => rowField('transfers', index, 'timing', e.target.value)} /></label><label><span>\u6765\u81ea\u7403\u961f ID</span><input value={String(row.from_team_id ?? '')} onChange={(e) => rowField('transfers', index, 'from_team_id', e.target.value)} /></label><label><span>\u53bb\u5f80\u7403\u961f ID</span><input value={String(row.to_team_id ?? '')} onChange={(e) => rowField('transfers', index, 'to_team_id', e.target.value)} /></label></div><button type="button" onClick={() => field('transfers', form.transfers.filter((_, current) => current !== index))}>\u5220\u9664\u8bb0\u5f55</button></div>)}</div><button type="button" onClick={() => field('transfers', [...form.transfers, { type: null, timing: null, from_team_id: null, to_team_id: null }])}>+ \u6dfb\u52a0\u8f6c\u4f1a</button></details>
        <details><summary>\u91cc\u7a0b\u7891\uff08\u53ef\u9009\uff09</summary><div className="admin-repeat-list">{form.milestones.map((row, index) => <div className="admin-repeat-row" key={index}><div className="admin-form-grid"><label><span>\u7c7b\u578b</span><input value={String(row.type ?? '')} onChange={(e) => rowField('milestones', index, 'type', e.target.value)} /></label><label><span>\u8bf4\u660e</span><input value={String(row.description ?? '')} onChange={(e) => rowField('milestones', index, 'description', e.target.value)} /></label></div><button type="button" onClick={() => field('milestones', form.milestones.filter((_, current) => current !== index))}>\u5220\u9664\u8bb0\u5f55</button></div>)}</div><button type="button" onClick={() => field('milestones', [...form.milestones, { type: null, description: null }])}>+ \u6dfb\u52a0\u91cc\u7a0b\u7891</button></details>
        <button className="admin-primary" type="submit" disabled={saving || !season}>{saving ? '\u4fdd\u5b58\u4e2d\u2026' : '\u4fdd\u5b58\u7403\u5458'}</button>{notice && <p className="admin-success">{notice}</p>}{error && <p className="admin-error">{error}</p>}
      </form>
    </div>
  </section>
}
