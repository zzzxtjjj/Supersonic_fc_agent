import { Link } from 'react-router-dom'
import type { Player, PlayerSeason } from '../../types'
import { PlayerAvatar } from './PlayerAvatar'

interface PlayerCardProps {
  player: Player
  seasonData: PlayerSeason | null
}

export function PlayerCard({ player, seasonData }: PlayerCardProps) {
  return (
    <Link className="player-card" to={`/players/${player.id}`}>
      <div className="player-card-topline">
        <span className="season-tag">{seasonData?.season ?? '暂无赛季'}</span>
        <span className="card-arrow" aria-hidden="true">
          ↗
        </span>
      </div>
      <PlayerAvatar name={player.name} avatarUrl={player.photoUrl} />
      <div className="player-card-body">
        <span className="player-number">
          {seasonData?.number === null || seasonData?.number === undefined
            ? '—'
            : `${seasonData.number}号`}
        </span>
        <div>
          <h2>
            {player.name}{seasonData?.isCaptain ? ' (C)' : ''}
          </h2>
          <p>
            {player.profileComplete
              ? seasonData?.position ?? '资料待补充'
              : '资料待补充'}
          </p>
        </div>
      </div>
    </Link>
  )
}
