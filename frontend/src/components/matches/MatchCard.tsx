import type { Match } from '../../types'
import { TeamCrest } from '../teams/TeamCrest'

interface MatchCardProps {
  match: Match
}

export function MatchCard({ match }: MatchCardProps) {
  const supersonicIsHome = match.homeTeam.id === 'supersonic'
  const goalsFor = supersonicIsHome ? match.homeScore : match.awayScore
  const goalsAgainst = supersonicIsHome ? match.awayScore : match.homeScore
  const result =
    goalsFor > goalsAgainst
      ? '胜'
      : goalsFor < goalsAgainst
        ? '负'
        : '平'
  const stageLabel =
    match.stage === 'regular'
      ? `常规赛第 ${match.round} 轮`
      : `季后赛半决赛${match.leg === 1 ? '首回合' : '次回合'}`

  return (
    <article className="match-card">
      <div className="match-meta">
        <span>{stageLabel}</span>
        <span>{match.competition}</span>
      </div>
      <div className="match-scoreline">
        <div className="team-name home-team">
          <TeamCrest team={match.homeTeam} />
          <span>
            <strong>{match.homeTeam.name}</strong>
            <small>{match.homeTeam.id === 'supersonic' ? 'SUPERSONIC FC' : 'HOME'}</small>
          </span>
        </div>
        <div className="score-block">
          <span className={`result-badge result-${result}`}>{result}</span>
          <strong>
            {match.homeScore}<i>:</i>{match.awayScore}
          </strong>
        </div>
        <div className="team-name away-team">
          <span>
            <strong>{match.awayTeam.name}</strong>
            <small>{match.awayTeam.id === 'supersonic' ? 'SUPERSONIC FC' : 'AWAY'}</small>
          </span>
          <TeamCrest team={match.awayTeam} />
        </div>
      </div>
      <div className="match-contributors">
        <span>超音速进球</span>
        {match.scorers.length ? (
          <div className="scorer-list">
            {match.scorers.map((scorer, index) => (
              <span
                className={`scorer-entry scorer-${scorer.type}`}
                key={`${scorer.type}-${scorer.playerId ?? 'own'}-${index}`}
              >
                <strong>
                  {scorer.type === 'own_goal' ? '对手乌龙' : scorer.playerName}
                  {scorer.goals > 1 ? ` ×${scorer.goals}` : ''}
                </strong>
                {scorer.note ? <small>（{scorer.note}）</small> : null}
              </span>
            ))}
          </div>
        ) : (
          <p>本场无进球</p>
        )}
      </div>
    </article>
  )
}
