import { useEffect, useState } from 'react'
import type { Team } from '../../types'

interface TeamCrestProps {
  team: Team
  size?: 'small' | 'large'
}

export function TeamCrest({ team, size = 'large' }: TeamCrestProps) {
  const [failed, setFailed] = useState(false)

  useEffect(() => setFailed(false), [team.crestUrl])

  if (team.crestUrl && !failed) {
    return (
      <span className={`team-crest ${size}`} data-team-id={team.id}>
        <img
          src={team.crestUrl}
          alt={`${team.name}队徽`}
          onError={() => setFailed(true)}
        />
      </span>
    )
  }

  return (
    <span
      className={`team-crest team-crest-placeholder ${size}`}
      data-team-id={team.id}
      aria-label={`${team.name}队徽占位`}
      title="队徽待上传"
    >
      队
    </span>
  )
}
