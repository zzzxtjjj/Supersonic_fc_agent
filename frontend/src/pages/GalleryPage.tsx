import { useEffect, useState } from 'react'
import { PhotoTile } from '../components/gallery/PhotoTile'
import { EmptyState } from '../components/layout/EmptyState'
import { PageHeader } from '../components/layout/PageHeader'
import { SeasonSelector } from '../components/SeasonSelector'
import { mediaData } from '../services/mediaData'
import type {
  MediaOptions,
  Photo,
  Season,
} from '../types'

type GallerySection = 'player' | 'team_group'

export function GalleryPage() {
  const [season, setSeason] = useState<Season>('25-26')
  const [section, setSection] = useState<GallerySection>('player')
  const [playerId, setPlayerId] = useState('')
  const [photos, setPhotos] = useState<Photo[]>([])
  const [options, setOptions] = useState<MediaOptions | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const controller = new AbortController()
    mediaData
      .getOptions(season, controller.signal)
      .then(setOptions)
      .catch(() => {
        if (!controller.signal.aborted) setOptions(null)
      })
    return () => controller.abort()
  }, [season])

  useEffect(() => {
    const controller = new AbortController()
    setLoading(true)
    setError(null)
    mediaData
      .getGallery(
        {
          season,
          category: section,
          playerId: section === 'player' ? playerId || undefined : undefined,
        },
        controller.signal,
      )
      .then(setPhotos)
      .catch((requestError: unknown) => {
        if (!controller.signal.aborted) {
          setError(
            requestError instanceof Error
              ? requestError.message
              : '无法加载照片',
          )
        }
      })
      .finally(() => {
        if (!controller.signal.aborted) setLoading(false)
    })
    return () => controller.abort()
  }, [season, section, playerId])

  function changeSeason(nextSeason: Season) {
    setSeason(nextSeason)
    setPlayerId('')
  }

  function changeSection(nextSection: GallerySection) {
    setSection(nextSection)
    setPlayerId('')
  }

  return (
    <div className="page">
      <section className="content-wrap">
        <PageHeader
          eyebrow="CLUB GALLERY"
          title="照片集"
          description="按赛季浏览个人照片与球队合照。"
          aside={<SeasonSelector value={season} onChange={changeSeason} />}
        />

        <section className="gallery-section">
          <div className="gallery-section-tabs" role="tablist" aria-label="照片板块">
            <button
              type="button"
              role="tab"
              aria-selected={section === 'player'}
              className={section === 'player' ? 'active' : undefined}
              onClick={() => changeSection('player')}
            >
              个人照片
            </button>
            <button
              type="button"
              role="tab"
              aria-selected={section === 'team_group'}
              className={section === 'team_group' ? 'active' : undefined}
              onClick={() => changeSection('team_group')}
            >
              球队合照
            </button>
          </div>

          {section === 'player' && (
            <div className="gallery-player-filter">
              <label htmlFor="gallery-player">按球员分类</label>
              <select
                id="gallery-player"
                value={playerId}
                onChange={(event) => setPlayerId(event.target.value)}
              >
                <option value="">全部球员</option>
                {options?.players.map((player) => (
                  <option key={player.id} value={player.id}>{player.name}</option>
                ))}
              </select>
            </div>
          )}

          <div className="section-heading compact-heading">
            <div>
              <p className="section-kicker">{season} · CLUB GALLERY</p>
              <h2>{section === 'player' ? '个人照片' : '球队合照'}</h2>
            </div>
            <span>{photos.length ? `${photos.length} 张` : '暂无图片'}</span>
          </div>

          {loading ? (
            <EmptyState label="正在加载照片…" />
          ) : error ? (
            <EmptyState label={`照片加载失败：${error}`} />
          ) : photos.length ? (
            <div className="gallery-grid">
              {photos.map((photo) => <PhotoTile key={photo.id} photo={photo} />)}
            </div>
          ) : (
            <EmptyState
              label={
                section === 'player'
                  ? `${season} 赛季暂无该球员照片`
                  : `${season} 赛季暂无球队合照`
              }
            />
          )}
        </section>
      </section>
    </div>
  )
}
