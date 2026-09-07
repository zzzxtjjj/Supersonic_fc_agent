import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { EmptyState } from '../components/layout/EmptyState'
import { PageHeader } from '../components/layout/PageHeader'
import { SeasonSelector } from '../components/SeasonSelector'
import { TeamCrest } from '../components/teams/TeamCrest'
import { seasonData } from '../services/seasonData'
import type { Match, Season } from '../types'

function matchLabel(match: Match) {
  if (match.stage === 'regular') return `第 ${match.round ?? '—'} 轮`
  return `季后赛${match.leg ? ` · 第${match.leg}回合` : ''}`
}

export function RatingsPage() {
  const [season, setSeason] = useState<Season>('25-26')
  const [matches, setMatches] = useState<Match[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const controller = new AbortController()
    setLoading(true)
    setError(null)
    seasonData.getMatches(season, controller.signal)
      .then(setMatches)
      .catch((requestError: unknown) => {
        if (!controller.signal.aborted) setError(requestError instanceof Error ? requestError.message : '比赛加载失败')
      })
      .finally(() => { if (!controller.signal.aborted) setLoading(false) })
    return () => controller.abort()
  }, [season])

  return (
    <div className="page rating-home-page">
      <section className="content-wrap">
        <PageHeader eyebrow="TEAM COMMUNITY" title="比赛评分" description="选择一场比赛，查看球队评分、Fan MVP 与球员讨论。" aside={<SeasonSelector value={season} onChange={setSeason} />} />
        <div className="section-heading"><div><p className="section-kicker">单场评分 · {season}</p><h2>选择比赛</h2></div><span>{matches.length ? `${matches.length} 场` : '等待数据'}</span></div>
        {loading ? <EmptyState label="正在加载可评分比赛…" /> : error ? <EmptyState label={`比赛加载失败：${error}`} /> : matches.length ? (
          <div className="rating-match-grid">
            {matches.map((match) => (
              <Link className="rating-match-card" key={match.id} to={`/ratings/matches/${match.id}`}>
                <header><span>{matchLabel(match)}</span>{match.date ? <time>{match.date.replaceAll('-', '.')}</time> : null}</header>
                <div><TeamCrest team={match.homeTeam} size="small" /><strong>{match.homeTeam.name}</strong><b>{match.homeScore} : {match.awayScore}</b><strong>{match.awayTeam.name}</strong><TeamCrest team={match.awayTeam} size="small" /></div>
                <footer>{match.competition}<span>进入评分 →</span></footer>
              </Link>
            ))}
          </div>
        ) : <EmptyState label={`${season} 赛季暂无比赛`} />}
      </section>
    </div>
  )
}
