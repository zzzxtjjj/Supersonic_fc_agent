import { useEffect, useState } from 'react'

interface PlayerAvatarProps {
  name: string
  avatarUrl: string | null
  size?: 'tiny' | 'small' | 'large'
}

export function PlayerAvatar({ name, avatarUrl, size = 'small' }: PlayerAvatarProps) {
  const className = `player-avatar ${size}`
  const [failed, setFailed] = useState(false)

  useEffect(() => setFailed(false), [avatarUrl])

  if (avatarUrl && !failed) {
    return (
      <img
        className={className}
        src={avatarUrl}
        alt={`${name}头像`}
        onError={() => setFailed(true)}
      />
    )
  }

  return (
    <div className={className} aria-label={`${name}头像占位`}>
      {name.slice(-1)}
    </div>
  )
}
