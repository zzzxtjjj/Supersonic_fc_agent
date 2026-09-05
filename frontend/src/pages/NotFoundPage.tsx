import { Link } from 'react-router-dom'
import { EmptyState } from '../components/layout/EmptyState'

export function NotFoundPage() {
  return (
    <div className="page">
      <section className="content-wrap narrow-content">
        <EmptyState label="这个页面不存在" />
        <Link className="text-link" to="/ai">返回 AI Agent</Link>
      </section>
    </div>
  )
}
