interface AdminSeasonSelectProps {
  seasons: string[]
  value: string
  onChange: (value: string) => void
}

export function AdminSeasonSelect({ seasons, value, onChange }: AdminSeasonSelectProps) {
  return (
    <label className="admin-season-select">
      <span>Season</span>
      <select value={value} onChange={(event) => onChange(event.target.value)}>
        {seasons.length ? seasons.map((season) => <option key={season} value={season}>{season}</option>) : <option value="">暂无赛季</option>}
      </select>
    </label>
  )
}
