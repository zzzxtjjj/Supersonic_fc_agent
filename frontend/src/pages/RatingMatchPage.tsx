import { useCallback, useEffect, useState } from 'react'
import { Link, useLocation, useNavigate, useParams } from 'react-router-dom'
import { CommentDrawer } from '../components/rating/CommentDrawer'
import { FanMvpCard } from '../components/rating/FanMvpCard'
import { PlayerAuthStatus } from '../components/rating/PlayerAuthStatus'
import { PlayerRatingCard } from '../components/rating/PlayerRatingCard'
import { RatingMatchHero } from '../components/rating/RatingMatchHero'
import { ratingData } from '../services/ratingData'
import type { RatingMatchResponse, RatingPlayer } from '../types/rating'

export function RatingMatchPage() {
  const { matchId = '' } = useParams()
  const navigate = useNavigate()
  const location = useLocation()
  const [data, setData] = useState<RatingMatchResponse | null>(null)
  const [selectedPlayer, setSelectedPlayer] = useState<RatingPlayer | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const load = useCallback(async () => {
    const result = await ratingData.getMatch(matchId)
    setData(result)
    setSelectedPlayer((current) => current ? result.players.find((player) => player.playerId === current.playerId) ?? null : null)
  }, [matchId])

  useEffect(() => {
    setLoading(true)
    setError(null)
    load().catch((requestError: unknown) => setError(requestError instanceof Error ? requestError.message : '评分页加载失败')).finally(() => setLoading(false))
  }, [load])

  const requireLogin = () => navigate('/player/login', { state: { from: location.pathname } })

  if (loading) return <div className="page"><div className="content-wrap rating-page-state">正在加载比赛评分…</div></div>
  if (error || !data) return <div className="page"><div className="content-wrap rating-page-state error">评分页加载失败：{error ?? '未知错误'}<Link to="/ratings">返回评分</Link></div></div>

  return (
    <div className="page rating-match-page">
      <section className="content-wrap">
        <Link className="back-link" to="/ratings">← 返回比赛选择</Link>
        <RatingMatchHero match={data.match} />
        <PlayerAuthStatus viewer={data.viewer} />
        {data.fanMvp && <FanMvpCard player={data.fanMvp} />}
        <div className="section-heading rating-squad-heading"><div><p className="section-kicker">FULL SQUAD</p><h2>球员评分</h2></div><span>{data.players.length} 名球员</span></div>
        <div className="rating-player-grid">
          {data.players.map((player) => (
            <PlayerRatingCard key={player.playerId} matchId={data.match.id} player={player} viewer={data.viewer} onRefresh={load} onOpenComments={setSelectedPlayer} onRequireLogin={requireLogin} />
          ))}
        </div>
      </section>
      <CommentDrawer matchId={data.match.id} player={selectedPlayer} viewer={data.viewer} onClose={() => setSelectedPlayer(null)} onChanged={load} onRequireLogin={requireLogin} />
    </div>
  )
}
