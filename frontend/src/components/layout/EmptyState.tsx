interface EmptyStateProps {
  label: string
  compact?: boolean
}

export function EmptyState({ label, compact = false }: EmptyStateProps) {
  return (
    <div className={compact ? 'empty-state compact' : 'empty-state'}>
      <span className="empty-icon" aria-hidden="true">
        —
      </span>
      <p>{label}</p>
    </div>
  )
}
