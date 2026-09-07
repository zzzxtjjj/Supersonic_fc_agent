import { useEffect, useState, type FormEvent } from 'react'
import { Link } from 'react-router-dom'
import { ratingData } from '../../services/ratingData'
import type { CommunityComment, RatingPlayer, ViewerPermissions } from '../../types/rating'
import { PlayerAvatar } from '../players/PlayerAvatar'

interface CommentDrawerProps {
  matchId: string
  player: RatingPlayer | null
  viewer: ViewerPermissions
  onClose: () => void
  onChanged: () => Promise<void>
  onRequireLogin: () => void
}

function formatTime(value: string) {
  const date = new Date(value)
  return Number.isNaN(date.getTime()) ? value : date.toLocaleString('zh-CN', { month: 'numeric', day: 'numeric', hour: '2-digit', minute: '2-digit' })
}

export function CommentDrawer({ matchId, player, viewer, onClose, onChanged, onRequireLogin }: CommentDrawerProps) {
  const [comments, setComments] = useState<CommunityComment[]>([])
  const [content, setContent] = useState('')
  const [loading, setLoading] = useState(false)
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!player) return
    setLoading(true)
    setError(null)
    ratingData.getComments(matchId, player.playerId)
      .then(setComments)
      .catch((requestError: unknown) => setError(requestError instanceof Error ? requestError.message : '评论加载失败'))
      .finally(() => setLoading(false))
  }, [matchId, player])

  if (!player) return null

  async function submit(event: FormEvent) {
    event.preventDefault()
    if (!viewer.authenticated) return onRequireLogin()
    if (!content.trim()) return
    setSubmitting(true)
    setError(null)
    try {
      const created = await ratingData.createComment(matchId, player!.playerId, content.trim())
      setComments((items) => [created, ...items])
      setContent('')
      await onChanged()
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : '评论发布失败')
    } finally {
      setSubmitting(false)
    }
  }

  async function like(comment: CommunityComment) {
    if (!viewer.authenticated) return onRequireLogin()
    const previous = comments
    setComments((items) => items.map((item) => item.id === comment.id ? {
      ...item,
      likedByMe: !item.likedByMe,
      likeCount: item.likeCount + (item.likedByMe ? -1 : 1),
    } : item))
    try {
      const result = await ratingData.likeComment(comment.id)
      setComments((items) => items.map((item) => item.id === comment.id ? {
        ...item,
        likedByMe: result.liked,
        likeCount: result.like_count,
      } : item))
      await onChanged()
    } catch (requestError) {
      setComments(previous)
      setError(requestError instanceof Error ? requestError.message : '点赞失败')
    }
  }

  return (
    <div className="comment-drawer-backdrop" role="presentation" onMouseDown={onClose}>
      <aside className="comment-drawer" role="dialog" aria-modal="true" aria-label={`${player.name}本场讨论`} onMouseDown={(event) => event.stopPropagation()}>
        <header>
          <div><p className="section-kicker">MATCH DISCUSSION</p><h2>{player.name} · 本场讨论</h2></div>
          <button type="button" onClick={onClose} aria-label="关闭评论">×</button>
        </header>
        <div className="comment-list">
          {loading ? <p className="drawer-state">正在加载评论…</p> : comments.length ? comments.map((comment) => (
            <article className="comment-item" key={comment.id}>
              <PlayerAvatar name={comment.author.name} avatarUrl={comment.author.photoUrl} size="tiny" />
              <div><strong>{comment.author.name}</strong><p>{comment.content}</p><time>{formatTime(comment.updatedAt)}</time></div>
              <button type="button" onClick={() => like(comment)}>{comment.likedByMe ? '♥' : '♡'} {comment.likeCount}</button>
            </article>
          )) : <p className="drawer-state">暂无评论，来记录本场感受吧。</p>}
        </div>
        {viewer.canComment ? (
          <form className="comment-composer" onSubmit={submit}>
            <label><span>发表评论 <i>{content.length} / 100</i></span><textarea rows={3} maxLength={100} value={content} onChange={(event) => setContent(event.target.value)} /></label>
            <button type="submit" disabled={submitting || !content.trim()}>{submitting ? '发布中…' : '发布评论'}</button>
          </form>
        ) : (
          <div className="drawer-login-prompt"><span>登录后参与讨论</span><Link to="/player/login">球员登录</Link></div>
        )}
        {error && <p className="inline-form-error drawer-error">{error}</p>}
      </aside>
    </div>
  )
}
