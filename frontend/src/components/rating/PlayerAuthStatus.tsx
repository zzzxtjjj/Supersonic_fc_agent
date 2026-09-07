import { Link } from 'react-router-dom'
import type { ViewerPermissions } from '../../types/rating'

export function PlayerAuthStatus({ viewer }: { viewer: ViewerPermissions }) {
  if (!viewer.authenticated) {
    return (
      <section className="rating-viewer-status guest">
        <div>
          <strong>登录后参与球队评分与讨论</strong>
          <span>游客可以查看所有评分、评论与 Fan MVP</span>
        </div>
        <Link to="/player/login">球员登录</Link>
      </section>
    )
  }
  return (
    <section className="rating-viewer-status verified">
      <span aria-hidden="true">✓</span>
      <div>
        <strong>已认证超音速球员</strong>
        <p>
          {viewer.canRate ? '本场可评分' : '本赛季不可评分'} ·{' '}
          {viewer.canComment ? '可评论' : '不可评论'} ·{' '}
          {viewer.canLike ? '可点赞' : '不可点赞'}
        </p>
      </div>
    </section>
  )
}
