import { seasons } from '../data/mockData'
import type { Season } from '../types'

interface SeasonSelectorProps {
  value: Season
  onChange: (season: Season) => void
  label?: string
}

export function SeasonSelector({
  value,
  onChange,
  label = '选择赛季',
}: SeasonSelectorProps) {
  return (
    <div className="season-control">
      <span>{label}</span>
      <div className="season-toggle" role="group" aria-label={label}>
        {seasons.map((season) => (
          <button
            key={season}
            type="button"
            className={value === season ? 'active' : undefined}
            aria-pressed={value === season}
            onClick={() => onChange(season)}
          >
            {season}
          </button>
        ))}
      </div>
    </div>
  )
}
