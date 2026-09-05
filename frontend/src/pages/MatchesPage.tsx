import { useEffect, useState } from 'react'
import { EmptyState } from '../components/layout/EmptyState'
import { PageHeader } from '../components/layout/PageHeader'
import { MatchCard } from '../components/matches/MatchCard'
import { SeasonSelector } from '../components/SeasonSelector'
import { seasonData } from '../services/seasonData'
import type { Match, Season } from '../types'

export function MatchesPage() {
  const [season, setSeason] = useState<Season>('25-26')
  const [matches, setMatches] = useState<Match[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const controller = new AbortController()
    setLoading(true)
    setError(null)

    seasonData
      .getMatches(season, controller.signal)
      .then(setMatches)
      .catch((requestError: unknown) => {
        if (!controller.signal.aborted) {
          setMatches([])
          setError(
            requestError instanceof Error
              ? requestError.message
              : '无法加载比赛数据',
          )
        }
      })
      .finally(() => {
        if (!controller.signal.aborted) setLoading(false)
      })

    return () => controller.abort()
  }, [season])

  const regularMatches = matches.filter((match) => match.stage === 'regular')
  const playoffMatches = matches.filter(
    (match) => match.stage === 'playoff_semifinal',
  )

  return (
    <div className="page">
      <section className="content-wrap">
        <PageHeader
          eyebrow="FIXTURES & RESULTS"
          title="比赛"
          description="按赛季查看超音速的比赛结果与已确认进球信息。"
          aside={<SeasonSelector value={season} onChange={setSeason} />}
        />

        <div className="section-heading">
          <div>
            <p className="section-kicker">MATCH CENTRE · {season}</p>
            <h2>比赛信息流</h2>
          </div>
          <span>{matches.length ? `${matches.length} 场已录入` : '等待数据'}</span>
        </div>

        {loading ? (
          <EmptyState label="正在加载赛季比赛数据…" />
        ) : error ? (
          <EmptyState label={`比赛数据加载失败：${error}`} />
        ) : matches.length ? (
          <div className="match-groups">
            <section className="match-group">
              <div className="match-group-title">
                <h3>常规赛</h3>
                <span>{regularMatches.length} 场</span>
              </div>
              <div className="match-list">
                {regularMatches.map((match) => (
                  <MatchCard key={match.id} match={match} />
                ))}
              </div>
            </section>

            <section className="match-group playoff-group">
              <div className="match-group-title">
                <h3>季后赛</h3>
                <span>{playoffMatches.length} 场</span>
              </div>
              <div className="match-list">
                {playoffMatches.map((match) => (
                  <MatchCard key={match.id} match={match} />
                ))}
              </div>
            </section>
          </div>
        ) : (
          <EmptyState label={`${season} 赛季数据暂未录入`} />
        )}
      </section>
    </div>
  )
}
