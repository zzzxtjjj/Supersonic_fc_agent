import { useEffect, useState } from 'react'
import { EmptyState } from '../components/layout/EmptyState'
import { PageHeader } from '../components/layout/PageHeader'
import { PlayerCard } from '../components/players/PlayerCard'
import { SeasonSelector } from '../components/SeasonSelector'
import { seasonData } from '../services/seasonData'
import type { PlayerListItem, Season } from '../types'

export function PlayersPage() {
  const [season, setSeason] = useState<Season>('25-26')
  const [players, setPlayers] = useState<PlayerListItem[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const controller = new AbortController()
    setLoading(true)
    setError(null)

    seasonData
      .getPlayers(season, controller.signal)
      .then(setPlayers)
      .catch((requestError: unknown) => {
        if (!controller.signal.aborted) {
          setPlayers([])
          setError(
            requestError instanceof Error
              ? requestError.message
              : '无法加载球员数据',
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
          eyebrow="THE SQUAD"
          title="球员"
          description="按赛季查看球衣号码与场上位置。点击球员卡片进入个人页面。"
          aside={<SeasonSelector value={season} onChange={setSeason} />}
        />

        <div className="section-heading">
          <div>
            <p className="section-kicker">ROSTER · {season}</p>
            <h2>球队阵容</h2>
          </div>
          <span>{players.length ? `${players.length} 名已录入球员` : '等待数据'}</span>
        </div>

        {loading ? (
          <EmptyState label="正在加载赛季球员数据…" />
        ) : error ? (
          <EmptyState label={`球员数据加载失败：${error}`} />
        ) : players.length ? (
          <div className="player-grid">
            {players.map((item) => (
              <PlayerCard
                key={item.player.id}
                player={item.player}
                seasonData={item.season}
              />
            ))}
          </div>
        ) : (
          <EmptyState label={`${season} 赛季数据暂未录入`} />
        )}
      </section>
    </div>
  )
}
