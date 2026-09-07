import { useEffect, useState } from 'react'
import { ratingData } from '../../services/ratingData'
import type { RatingPlayer, ViewerPermissions } from '../../types/rating'
import { PlayerAvatar } from '../players/PlayerAvatar'
import { RatingInput } from './RatingInput'

interface PlayerRatingCardProps {
  matchId: string
  player: RatingPlayer
  viewer: ViewerPermissions
  onRefresh: () => Promise<void>
  onOpenComments: (player: RatingPlayer) => void
  onRequireLogin: () => void
}

export function PlayerRatingCard({
  matchId,
  player,
  viewer,
  onRefresh,
  onOpenComments,
  onRequireLogin,
}: PlayerRatingCardProps) {
  const [score, setScore] = useState(player.rating.myScore ?? 7.5)
  const [saving, setSaving] = useState(false)
  const [saved, setSaved] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    setScore(player.rating.myScore ?? 7.5)
  }, [player.rating.myScore])

  async function submit() {
    if (!viewer.authenticated) return onRequireLogin()
    if (!viewer.canRate) {
      setError('你没有这个赛季的评分权限')
      return
    }
    setSaving(true)
    setSaved(false)
    setError(null)
    try {
      await ratingData.submitRating(matchId, player.playerId, score)
      await onRefresh()
      setSaved(true)
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : '评分保存失败')
    } finally {
      setSaving(false)
    }
  }

  async function likeTopComment(commentId: string) {
    if (!viewer.authenticated) return onRequireLogin()
    try {
      await ratingData.likeComment(commentId)
      await onRefresh()
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : '点赞失败')
    }
  }

  const facts = [
    player.matchFacts.goals ? `${player.matchFacts.goals}进球` : null,
    player.matchFacts.assists ? `${player.matchFacts.assists}助攻` : null,
  ].filter(Boolean)

  return (
    <article className="rating-player-card">
      <header>
        <PlayerAvatar name={player.name} avatarUrl={player.photoUrl} size="small" />
        <div>
          <span className="rating-shirt-number">#{player.number ?? '—'}</span>
          <h2>{player.name}</h2>
          {facts.length ? <p>{facts.join(' · ')}</p> : <p>本场暂无已确认进球/助攻</p>}
        </div>
        <div className="rating-average">
          {player.rating.average === null ? <strong>暂无评分</strong> : <b>{player.rating.average.toFixed(1)} 分</b>}
          <span>{player.rating.count}人评分</span>
        </div>
      </header>

      <section className="my-rating-panel">
        <div className="rating-panel-title">
          <strong>{player.rating.myScore === null ? '我的评分' : '修改我的评分'}</strong>
          {player.rating.myScore !== null && <span>已评 {player.rating.myScore.toFixed(1)}</span>}
        </div>
        <RatingInput value={score} onChange={setScore} disabled={saving || !viewer.canRate} />
        <button className="rating-submit" type="button" disabled={saving} onClick={submit}>
          {saving ? '保存中…' : saved ? '已保存 ✓' : player.rating.myScore === null ? '提交评分' : '保存修改'}
        </button>
        {error && <p className="inline-form-error">{error}</p>}
      </section>

      {player.topComment && (
        <section className="top-comment">
          <span>🔥 热评</span>
          <div>
            <PlayerAvatar name={player.topComment.author.name} avatarUrl={player.topComment.author.photoUrl} size="tiny" />
            <p><b>{player.topComment.author.name}：</b><span>{player.topComment.content}</span></p>
            <button type="button" onClick={() => likeTopComment(player.topComment!.id)}>
              {player.topComment.likedByMe ? '♥' : '♡'} {player.topComment.likeCount}
            </button>
          </div>
        </section>
      )}
      <button className="comments-link" type="button" onClick={() => onOpenComments(player)}>
        {player.commentCount ? `查看全部 ${player.commentCount} 条评论` : '发表第一条评论'} <span>›</span>
      </button>
    </article>
  )
}
