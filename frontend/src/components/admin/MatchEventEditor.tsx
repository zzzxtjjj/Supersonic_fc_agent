import type { AdminMatchEvent, AdminMatchEventType, AdminPlayer } from '../../types/admin'
import type { MediaOption } from '../../types'

interface MatchEventEditorProps {
  events: AdminMatchEvent[]
  players: AdminPlayer[]
  teams: MediaOption[]
  onChange: (events: AdminMatchEvent[]) => void
}

const types: Array<{ value: AdminMatchEventType; label: string }> = [
  { value: 'goal', label: 'Normal Goal' },
  { value: 'own_goal', label: 'Own Goal' },
  { value: 'substitution', label: '换人' },
  { value: 'yellow_card', label: '黄牌' },
  { value: 'red_card', label: '红牌' },
]

export function MatchEventEditor({ events, players, teams, onChange }: MatchEventEditorProps) {
  const update = (index: number, changes: Partial<AdminMatchEvent>) => onChange(events.map((event, current) => current === index ? { ...event, ...changes } : event))
  const add = () => onChange([...events, { type: 'goal', team_id: 'supersonic', scorer_player_id: null, assist_player_id: null, minute: null }])
  return (
    <section className="match-event-editor">
      <div className="admin-section-title"><div><p className="section-kicker">EVENT SOURCE OF TRUTH</p><h3>比赛事件</h3></div><button type="button" onClick={add}>+ 添加事件</button></div>
      {events.length ? <div className="event-editor-list">{events.map((event, index) => (
        <article key={`${index}-${event.type}`}>
          <label><span>分钟</span><input type="number" min="0" value={event.minute ?? ''} onChange={(e) => update(index, { minute: e.target.value ? Number(e.target.value) : null })} /></label>
          <label><span>类型</span><select value={event.type} onChange={(e) => update(index, { type: e.target.value as AdminMatchEventType, player_id: null, scorer_player_id: null, assist_player_id: null })}>{types.map((type) => <option key={type.value} value={type.value}>{type.label}</option>)}</select></label>
          {(event.type === 'goal' || event.type === 'own_goal') && <label><span>记分球队</span><select value={event.team_id ?? ''} onChange={(e) => update(index, { team_id: e.target.value })}><option value="">选择球队</option>{teams.map((team) => <option key={team.id} value={team.id}>{team.name}</option>)}</select></label>}
          {event.type === 'goal' && <><label><span>进球球员</span><select value={(event.scorer_player_id ?? event.player_id) ?? ''} onChange={(e) => update(index, { scorer_player_id: e.target.value || null, player_id: null })}><option value="">选择球员</option>{players.map((player) => <option key={player.id} value={player.id}>{player.name}</option>)}</select></label><label><span>助攻</span><select value={event.assist_player_id ?? ''} onChange={(e) => update(index, { assist_player_id: e.target.value || null })}><option value="">无助攻 / 未确认</option>{players.map((player) => <option key={player.id} value={player.id}>{player.name}</option>)}</select></label></>}
          {event.type === 'substitution' && <><label><span>换上</span><select value={event.player_in_id ?? ''} onChange={(e) => update(index, { player_in_id: e.target.value || null })}><option value="">选择球员</option>{players.map((player) => <option key={player.id} value={player.id}>{player.name}</option>)}</select></label><label><span>换下</span><select value={event.player_out_id ?? ''} onChange={(e) => update(index, { player_out_id: e.target.value || null })}><option value="">选择球员</option>{players.map((player) => <option key={player.id} value={player.id}>{player.name}</option>)}</select></label></>}
          {(event.type === 'yellow_card' || event.type === 'red_card') && <label><span>球员</span><select value={event.player_id ?? ''} onChange={(e) => update(index, { player_id: e.target.value || null })}><option value="">选择球员</option>{players.map((player) => <option key={player.id} value={player.id}>{player.name}</option>)}</select></label>}
          <label className="event-note"><span>备注</span><input value={event.note ?? ''} onChange={(e) => update(index, { note: e.target.value || null })} /></label>
          <button className="event-delete" type="button" onClick={() => onChange(events.filter((_, current) => current !== index))}>删除</button>
        </article>
      ))}</div> : <p className="admin-empty-inline">暂无事件。有进球的新比赛必须添加 Goal / Own Goal 事件。</p>}
      <p className="admin-help-text">“无助攻 / 未确认”会发送 null，系统不会自动猜测助攻者。Own Goal 不要选择超音速进球球员。</p>
    </section>
  )
}
