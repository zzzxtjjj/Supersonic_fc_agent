import { useEffect, useMemo, useState, type FormEvent } from 'react'
import { AdminSeasonSelect } from '../components/admin/AdminSeasonSelect'
import { MatchEventEditor } from '../components/admin/MatchEventEditor'
import { adminData } from '../services/adminData'
import { mediaData } from '../services/mediaData'
import type { MediaOption } from '../types'
import type { AdminMatch, AdminMatchEvent, AdminPlayer, AdminStatsPreview } from '../types/admin'

function emptyMatch(season: string): AdminMatch {
  return {
    id: '', season, competition: '\u8d85\u7ea7\u8054\u8d5b', stage: 'regular', round: null,
    date: null, home_team_id: 'supersonic', away_team_id: '', home_score: 0,
    away_score: 0, captain_player_id: null, goalkeeper_player_id: null, events: [],
  }
}

export function AdminMatchesPage() {
  const [seasons, setSeasons] = useState<string[]>([])
  const [season, setSeason] = useState('')
  const [matches, setMatches] = useState<AdminMatch[]>([])
  const [players, setPlayers] = useState<AdminPlayer[]>([])
  const [teams, setTeams] = useState<MediaOption[]>([])
  const [selectedId, setSelectedId] = useState<string | null>(null)
  const [draft, setDraft] = useState<AdminMatch>(emptyMatch(''))
  const [eventsTouched, setEventsTouched] = useState(false)
  const [preview, setPreview] = useState<AdminStatsPreview | null>(null)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [notice, setNotice] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)
  const selected = useMemo(() => matches.find((match) => match.id === selectedId) ?? null, [matches, selectedId])

  useEffect(() => {
    adminData.getSeasons().then((items) => { setSeasons(items); setSeason(items.at(-1) ?? '') })
      .catch((reason: unknown) => setError(reason instanceof Error ? reason.message : '\u8d5b\u5b63\u52a0\u8f7d\u5931\u8d25'))
  }, [])

  useEffect(() => {
    if (!season) { setLoading(false); return }
    const controller = new AbortController()
    setLoading(true); setError(null); setNotice(null); setSelectedId(null); setDraft(emptyMatch(season)); setEventsTouched(false)
    Promise.all([
      adminData.getMatches(season, controller.signal),
      adminData.getPlayers(season, controller.signal),
      mediaData.getOptions(season, controller.signal),
    ]).then(([matchItems, playerItems, options]) => {
      setMatches(matchItems); setPlayers(playerItems); setTeams(options.teams)
    }).catch((reason: unknown) => {
      if (!controller.signal.aborted) setError(reason instanceof Error ? reason.message : '\u6bd4\u8d5b\u6570\u636e\u52a0\u8f7d\u5931\u8d25')
    }).finally(() => { if (!controller.signal.aborted) setLoading(false) })
    return () => controller.abort()
  }, [season])

  function edit(match: AdminMatch) {
    setSelectedId(match.id); setDraft({ ...match, events: match.events ? match.events.map((event) => ({ ...event })) : undefined })
    setEventsTouched(false); setNotice(null); setError(null)
  }
  function createNew() { setSelectedId(null); setDraft(emptyMatch(season)); setEventsTouched(true); setNotice(null); setError(null) }
  function update<K extends keyof AdminMatch>(key: K, value: AdminMatch[K]) { setDraft((current) => ({ ...current, [key]: value })) }
  function updateEvents(events: AdminMatchEvent[]) { update('events', events); setEventsTouched(true) }
  const teamName = (id: string) => teams.find((team) => team.id === id)?.name ?? id

  async function save(event: FormEvent) {
    event.preventDefault(); setSaving(true); setError(null); setNotice(null)
    const payload: AdminMatch = { ...draft, season }
    if (!eventsTouched && selected && selected.events == null) delete payload.events
    try {
      const saved = selected ? await adminData.updateMatch(season, payload) : await adminData.createMatch(season, payload)
      setMatches((items) => selected ? items.map((item) => item.id === saved.id ? saved : item) : [...items, saved])
      setSelectedId(saved.id); setDraft(saved); setEventsTouched(false)
      setPreview(await adminData.getStatsPreview(season))
      setNotice('\u6bd4\u8d5b\u5df2\u4fdd\u5b58\uff0c\u8fdb\u7403\u4e0e\u52a9\u653b\u7edf\u8ba1\u9884\u89c8\u5df2\u5237\u65b0\u3002')
    } catch (reason) { setError(reason instanceof Error ? reason.message : '\u6bd4\u8d5b\u4fdd\u5b58\u5931\u8d25') } finally { setSaving(false) }
  }

  return <section className="admin-page">
    <header className="admin-page-header with-control"><div><p className="section-kicker">MATCH OPERATIONS</p><h1>\u6bd4\u8d5b\u4e0e\u4e8b\u4ef6</h1><p>\u6bd4\u5206\u4e0e Match Events \u4f5c\u4e3a\u7edf\u8ba1\u6765\u6e90\uff1b\u7a7a\u52a9\u653b\u4e0d\u4f1a\u88ab\u81ea\u52a8\u731c\u6d4b\u3002</p></div><AdminSeasonSelect seasons={seasons} value={season} onChange={setSeason} /></header>
    <div className="admin-editor-layout admin-match-layout">
      <section className="admin-card admin-record-list"><div className="admin-section-title"><h2>\u6bd4\u8d5b <small>{matches.length}</small></h2><button type="button" onClick={createNew}>+ \u65b0\u5efa\u6bd4\u8d5b</button></div>{loading ? <p>\u6b63\u5728\u52a0\u8f7d\u2026</p> : matches.length ? matches.map((match) => <button type="button" className={selectedId === match.id ? 'selected' : ''} key={match.id} onClick={() => edit(match)}><span><strong>{match.round ? `\u7b2c${match.round}\u8f6e \u00b7 ` : ''}{teamName(match.home_team_id)} {match.home_score}:{match.away_score} {teamName(match.away_team_id)}</strong><small>{match.date ?? '\u65e5\u671f\u5f85\u8865\u5145'} \u00b7 {match.id}</small></span></button>) : <p className="admin-empty-inline">\u8be5\u8d5b\u5b63\u6682\u65e0\u6bd4\u8d5b</p>}</section>
      <form className="admin-card admin-form admin-match-form" onSubmit={save}><div className="admin-section-title"><h2>{selected ? '\u7f16\u8f91\u6bd4\u8d5b' : '\u65b0\u5efa\u6bd4\u8d5b'}</h2>{selected && <button type="button" onClick={createNew}>\u53d6\u6d88\u7f16\u8f91</button>}</div>
        <div className="admin-form-grid"><label><span>Match ID</span><input value={draft.id} disabled={Boolean(selected)} pattern="[a-z0-9][a-z0-9-]*" onChange={(e) => update('id', e.target.value)} required /></label><label><span>\u65e5\u671f</span><input type="date" value={draft.date ?? ''} onChange={(e) => update('date', e.target.value || null)} /></label><label><span>\u8d5b\u4e8b</span><input value={draft.competition} onChange={(e) => update('competition', e.target.value)} required /></label><label><span>Stage</span><input value={draft.stage} onChange={(e) => update('stage', e.target.value)} required /></label><label><span>Round</span><input type="number" min="1" value={draft.round ?? ''} onChange={(e) => update('round', e.target.value ? Number(e.target.value) : null)} /></label><label><span>Leg</span><input type="number" min="1" value={draft.leg ?? ''} onChange={(e) => update('leg', e.target.value ? Number(e.target.value) : null)} /></label><label><span>Home Team</span><select value={draft.home_team_id} onChange={(e) => update('home_team_id', e.target.value)} required><option value="">\u9009\u62e9\u7403\u961f</option>{teams.map((team) => <option key={team.id} value={team.id}>{team.name}</option>)}</select></label><label><span>Away Team</span><select value={draft.away_team_id} onChange={(e) => update('away_team_id', e.target.value)} required><option value="">\u9009\u62e9\u7403\u961f</option>{teams.map((team) => <option key={team.id} value={team.id}>{team.name}</option>)}</select></label></div>
        <div className="admin-score-editor"><label><span>\u4e3b\u961f\u6bd4\u5206</span><input type="number" min="0" value={draft.home_score} onChange={(e) => update('home_score', Number(e.target.value))} /></label><strong>:</strong><label><span>\u5ba2\u961f\u6bd4\u5206</span><input type="number" min="0" value={draft.away_score} onChange={(e) => update('away_score', Number(e.target.value))} /></label></div>
        <div className="admin-form-grid"><label><span>\u961f\u957f</span><select value={draft.captain_player_id ?? ''} onChange={(e) => update('captain_player_id', e.target.value || null)}><option value="">\u672a\u586b\u5199</option>{players.map((player) => <option key={player.id} value={player.id}>{player.name}</option>)}</select></label><label><span>\u95e8\u5c06</span><select value={draft.goalkeeper_player_id ?? ''} onChange={(e) => update('goalkeeper_player_id', e.target.value || null)}><option value="">\u672a\u586b\u5199</option>{players.map((player) => <option key={player.id} value={player.id}>{player.name}</option>)}</select></label></div>
        <MatchEventEditor events={draft.events ?? []} players={players} teams={teams} onChange={updateEvents} />
        <button className="admin-primary" type="submit" disabled={saving || !season}>{saving ? '\u4fdd\u5b58\u4e2d\u2026' : '\u4fdd\u5b58\u6bd4\u8d5b'}</button>{notice && <p className="admin-success">{notice}</p>}{error && <p className="admin-error">{error}</p>}
        {preview && <div className="save-preview"><strong>\u7edf\u8ba1\u5df2\u5237\u65b0</strong><span>\u5c04\u624b\u699c {preview.scorers.length} \u4eba \u00b7 \u52a9\u653b\u699c {preview.assists.length} \u4eba</span></div>}
      </form>
    </div>
  </section>
}
