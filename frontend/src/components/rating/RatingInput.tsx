interface RatingInputProps {
  value: number
  onChange: (value: number) => void
  disabled?: boolean
}

export function RatingInput({ value, onChange, disabled }: RatingInputProps) {
  const change = (next: number) => {
    const clamped = Math.min(10, Math.max(0, next))
    onChange(Math.round(clamped * 10) / 10)
  }
  return (
    <div className="rating-input">
      <div className="rating-stepper">
        <button type="button" onClick={() => change(value - 0.1)} disabled={disabled || value <= 0}>−</button>
        <output>{value.toFixed(1)}</output>
        <button type="button" onClick={() => change(value + 0.1)} disabled={disabled || value >= 10}>+</button>
      </div>
      <label>
        <span>0</span>
        <input
          type="range"
          min="0"
          max="10"
          step="0.1"
          value={value}
          disabled={disabled}
          onChange={(event) => onChange(Number(event.target.value))}
          aria-label="评分，0到10分"
        />
        <span>10</span>
      </label>
    </div>
  )
}
