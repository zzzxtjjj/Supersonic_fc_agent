import { useEffect, useState } from 'react'
import { EmptyState } from '../components/layout/EmptyState'
import { PageHeader } from '../components/layout/PageHeader'
import { RankingTable } from '../components/stats/RankingTable'
import { TeamCrest } from '../components/teams/TeamCrest'
import { SeasonSelector } from '../components/SeasonSelector'
import { seasonData } from '../services/seasonData'
import type { RankingEntry, Season, Standing } from '../types'

export function StatsPage() {
  const [season, setSeason] = useState<Season>('25-26')
  const [standings, setStandings] = useState<Standing[]>([])
  const [scorers, setScorers] = useState<RankingEntry[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const controller = new AbortController()
    setLoading(true)
    setError(null)

    Promise.all([
      seasonData.getStandings(season, controller.signal),
      seasonData.getScorers(season, controller.signal),
    ])
      .then(([standingRows, scorerRows]) => {
        setStandings(standingRows)
        setScorers(scorerRows)
      })
      .catch((requestError: unknown) => {
        if (!controller.signal.aborted) {
          setStandings([])
          setScorers([])
          setError(
            requestError instanceof Error
              ? requestError.message
              : '无法加载统计数据',
          )
        }
      })
      .finally(() => {
        if (!controller.signal.aborted) setLoading(false)
      })

    return () => controller.abort()
  }, [season])

  return (
    <div className="page">
      <section className="content-wrap">
        <PageHeader
          eyebrow="NUMBERS OF THE SEASON"
          title="数据"
          description="聚合联赛排名与球队内部数据；只展示当前已确认的信息。"
          aside={<SeasonSelector value={season} onChange={setSeason} />}
        />

        {loading ? <EmptyState label="正在加载赛季统计数据…" /> : null}
        {!loading && error ? (
          <EmptyState label={`统计数据加载失败：${error}`} />
        ) : null}
        {!loading && !error && !standings.length && !scorers.length ? (
          <EmptyState label={`${season} 赛季数据暂未录入`} />
        ) : null}

        {!loading && !error && (standings.length || scorers.length) ? (
          <>
        <section className="stats-section standings-section">
          <div className="section-heading compact-heading">
            <div>
              <p className="section-kicker">LEAGUE TABLE</p>
              <h2>联赛积分榜</h2>
            </div>
          </div>
          {standings.length ? (
            <div className="table-scroll">
              <table className="data-table standings-table">
                <thead>
                  <tr>
                    <th>排名</th><th>球队</th><th>积分</th><th>净胜球</th><th>进球</th>
                  </tr>
                </thead>
                <tbody>
                  {standings.map((row) => (
                    <tr
                      key={row.teamId}
                      className={row.teamId === 'supersonic' ? 'is-supersonic' : undefined}
                    >
                      <td>{row.rank}</td>
                      <td>
                        <span className="standing-team">
                          <TeamCrest
                            team={{
                              id: row.teamId,
                              name: row.teamName,
                              crestUrl: row.crestUrl,
                            }}
                            size="small"
                          />
                          {row.teamName}
                        </span>
                      </td>
                      <td className="standing-points">{row.points}</td>
                      <td>{row.goalDifference > 0 ? '+' : ''}{row.goalDifference}</td>
                      <td>{row.goalsFor}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <EmptyState compact label={`${season}赛季暂无可靠积分榜数据`} />
          )}
        </section>

        <section className="stats-section">
            <div className="section-heading compact-heading">
              <div>
                <p className="section-kicker">GOALS</p>
                <h2>队内射手榜</h2>
              </div>
            </div>
            <RankingTable entries={scorers} valueLabel="进球" />
        </section>

        <p className="data-note">
          射手榜由比赛进球事件自动汇总；积分榜仅展示已提供的官方字段。
        </p>
          </>
        ) : null}
      </section>
    </div>
  )
}
