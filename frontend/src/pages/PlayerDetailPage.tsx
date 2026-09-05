import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { EmptyState } from '../components/layout/EmptyState'
import { PhotoTile } from '../components/gallery/PhotoTile'
import { PlayerAvatar } from '../components/players/PlayerAvatar'
import { SeasonSelector } from '../components/SeasonSelector'
import { ApiError } from '../services/api'
import { mediaData } from '../services/mediaData'
import { seasonData } from '../services/seasonData'
import type { Photo, PlayerDetail, Season } from '../types'

function display(value: string | number | null | undefined) {
  return value === null || value === undefined ? '暂无数据' : value
}

export function PlayerDetailPage() {
  const { id = '' } = useParams()
  const [season, setSeason] = useState<Season>('25-26')
  const [detail, setDetail] = useState<PlayerDetail | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [photos, setPhotos] = useState<Photo[]>([])
  const [photosLoading, setPhotosLoading] = useState(true)
  const [photosError, setPhotosError] = useState<string | null>(null)

  useEffect(() => {
    const controller = new AbortController()
    setLoading(true)
    setError(null)

    seasonData
      .getPlayer(id, controller.signal)
      .then(setDetail)
      .catch((requestError: unknown) => {
        if (!controller.signal.aborted) {
          setDetail(null)
          setError(
            requestError instanceof ApiError && requestError.status === 404
              ? '没有找到这名球员'
              : requestError instanceof Error
                ? `球员数据加载失败：${requestError.message}`
                : '球员数据加载失败',
          )
        }
      })
      .finally(() => {
        if (!controller.signal.aborted) setLoading(false)
      })

    return () => controller.abort()
  }, [id])

  useEffect(() => {
    const controller = new AbortController()
    setPhotosLoading(true)
    setPhotosError(null)

    mediaData
      .getGallery(
        { season, playerId: id, category: 'player' },
        controller.signal,
      )
      .then(setPhotos)
      .catch((requestError: unknown) => {
        if (!controller.signal.aborted) {
          setPhotos([])
          setPhotosError(
            requestError instanceof Error
              ? `球员照片加载失败：${requestError.message}`
              : '球员照片加载失败',
          )
        }
      })
      .finally(() => {
        if (!controller.signal.aborted) setPhotosLoading(false)
      })

    return () => controller.abort()
  }, [id, season])

  if (loading || error || !detail) {
    return (
      <div className="page">
        <section className="content-wrap narrow-content">
          <EmptyState label={loading ? '正在加载球员数据…' : error ?? '没有找到这名球员'} />
          <Link className="text-link" to="/players">
            返回球员列表
          </Link>
        </section>
      </div>
    )
  }

  const { player } = detail
  const selectedSeason = detail.seasons.find((item) => item.season === season)

  return (
    <div className="page">
      <section className="content-wrap">
        <Link className="back-link" to="/players">
          ← 返回球员列表
        </Link>

        <header className="player-hero">
          <PlayerAvatar name={player.name} avatarUrl={player.photoUrl} size="large" />
          <div className="player-identity">
            <p className="eyebrow">PLAYER PROFILE</p>
            <h1>{player.name}{selectedSeason?.isCaptain ? ' (C)' : ''}</h1>
            <p>
              {player.profileComplete
                ? selectedSeason?.position ?? '资料待补充'
                : '资料待补充'}
            </p>
          </div>
          <div className="hero-number" aria-label="球衣号码">
            <span>号码</span>
            <strong>
              {selectedSeason?.number === null || selectedSeason?.number === undefined
                ? '—'
                : `${selectedSeason.number}号`}
            </strong>
          </div>
        </header>

        <div className="detail-toolbar">
          <SeasonSelector value={season} onChange={setSeason} label="球员赛季" />
        </div>

        <div className="detail-grid">
          <section className="detail-section profile-facts">
            <div className="section-heading compact-heading">
              <div>
                <p className="section-kicker">IDENTITY</p>
                <h2>基本信息</h2>
              </div>
            </div>
            <dl>
              <div><dt>号码</dt><dd>{display(selectedSeason?.number)}</dd></div>
              <div><dt>位置</dt><dd>{display(selectedSeason?.position)}</dd></div>
              <div><dt>家乡</dt><dd>{display(player.hometown)}</dd></div>
              <div><dt>惯用脚</dt><dd>{display(player.dominantFoot)}</dd></div>
            </dl>
          </section>

          <section className="detail-section season-stats">
            <div className="section-heading compact-heading">
              <div>
                <p className="section-kicker">SEASON DATA</p>
                <h2>{season} 赛季数据</h2>
              </div>
            </div>
            <div className="stat-grid">
              <div><strong>{display(selectedSeason?.appearances)}</strong><span>出场</span></div>
              <div><strong>{display(selectedSeason?.goals)}</strong><span>进球</span></div>
              <div><strong>{display(selectedSeason?.assists)}</strong><span>助攻</span></div>
            </div>
          </section>

          <section className="detail-section technical-panel">
            <div className="section-heading compact-heading">
              <div>
                <p className="section-kicker">PLAY STYLE</p>
                <h2>技术特点</h2>
              </div>
            </div>
            {selectedSeason?.technicalProfile ? (
              <p>{selectedSeason.technicalProfile}</p>
            ) : (
              <EmptyState compact label="暂无技术特点数据" />
            )}
          </section>

          <section className="detail-section player-gallery-preview">
            <div className="section-heading compact-heading">
              <div>
                <p className="section-kicker">PLAYER PHOTOS</p>
                <h2>球员照片</h2>
              </div>
            </div>
            {photosLoading ? (
              <EmptyState compact label="正在加载球员照片…" />
            ) : photosError ? (
              <EmptyState compact label={photosError} />
            ) : photos.length ? (
              <div className="player-photo-grid">
                {photos.map((photo) => <PhotoTile key={photo.id} photo={photo} />)}
              </div>
            ) : (
              <EmptyState compact label={`${season} 赛季暂无球员照片`} />
            )}
          </section>
        </div>
      </section>
    </div>
  )
}
