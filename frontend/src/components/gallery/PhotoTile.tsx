import type { Photo } from '../../types'

interface PhotoTileProps {
  photo: Photo
}

export function PhotoTile({ photo }: PhotoTileProps) {
  const label = photo.caption ?? photo.title ?? photo.originalName
  const typeLabel = {
    player: '球员照片',
    team_group: '球队合照',
    team: '球队队徽',
  }[photo.type]

  return (
    <article className="photo-tile">
      <img src={photo.url} alt={label} loading="lazy" />
      <div className="photo-caption">
        <span>{photo.season ?? 'CLUB'} · {typeLabel}</span>
        <p>{label}</p>
      </div>
    </article>
  )
}
