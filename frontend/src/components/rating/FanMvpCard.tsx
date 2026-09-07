import type { FanMvp } from '../../types/rating'
import { PlayerAvatar } from '../players/PlayerAvatar'

export function FanMvpCard({ player }: { player: FanMvp }) {
  return (
    <section className="fan-mvp-card">
      <div>
        <p className="section-kicker">FAN MVP</p>
        <h2>🏆 Fan MVP</h2>
        <span>至少 3 人评分后产生</span>
      </div>
      <PlayerAvatar name={player.name} avatarUrl={player.photoUrl} size="small" />
      <div className="fan-mvp-person">
        <strong>{player.name}</strong>
        <span>{player.ratingCount}人评分</span>
      </div>
      <b>{player.average.toFixed(1)}</b>
    </section>
  )
}
