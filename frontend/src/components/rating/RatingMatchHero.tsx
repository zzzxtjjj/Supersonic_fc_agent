import type { RatingMatchSummary } from '../../types/rating'
import { TeamCrest } from '../teams/TeamCrest'

export function RatingMatchHero({ match }: { match: RatingMatchSummary }) {
  const roundLabel = match.round ? `第 ${match.round} 轮` : '淘汰赛'
  return (
    <section className="rating-match-hero">
      <p>{match.seasonId} {match.competition} · {roundLabel}</p>
      {match.date ? <time>{match.date.replaceAll('-', '.')}</time> : null}
      <div className="rating-scoreboard">
        <div>
          <TeamCrest team={match.homeTeam} size="large" />
          <strong>{match.homeTeam.name}</strong>
        </div>
        <span>{match.homeScore}<i>:</i>{match.awayScore}</span>
        <div>
          <TeamCrest team={match.awayTeam} size="large" />
          <strong>{match.awayTeam.name}</strong>
        </div>
      </div>
    </section>
  )
}
