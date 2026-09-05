import type { ReactNode } from 'react'

interface PageHeaderProps {
  eyebrow: string
  title: string
  description: string
  aside?: ReactNode
}

export function PageHeader({ eyebrow, title, description, aside }: PageHeaderProps) {
  return (
    <header className="page-header">
      <div>
        <p className="eyebrow">{eyebrow}</p>
        <h1>{title}</h1>
        <p className="page-description">{description}</p>
      </div>
      {aside ? <div className="page-header-aside">{aside}</div> : null}
    </header>
  )
}
