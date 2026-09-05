import { useEffect, useState, type DragEvent } from 'react'
import { useNavigate } from 'react-router-dom'
import { PageHeader } from '../components/layout/PageHeader'
import { adminAuth } from '../services/adminAuth'
import { mediaData } from '../services/mediaData'
import type {
  MediaCategory,
  MediaOptions,
  Photo,
  Season,
} from '../types'

interface SelectedImage {
  key: string
  file: File
  previewUrl: string
  playerId: string
}

const categories: { value: MediaCategory; label: string }[] = [
  { value: 'player', label: '球员照片' },
  { value: 'team_group', label: '球队合照' },
  { value: 'team', label: '球队队徽' },
]

const acceptedExtensions = /\.(?:jpe?g|png|webp)$/i

export function MediaAdminPage() {
  const navigate = useNavigate()
  const [category, setCategory] = useState<MediaCategory>('team_group')
  const [season, setSeason] = useState<Season | ''>('25-26')
  const [options, setOptions] = useState<MediaOptions | null>(null)
  const [files, setFiles] = useState<SelectedImage[]>([])
  const [teamId, setTeamId] = useState('')
  const [title, setTitle] = useState('')
  const [caption, setCaption] = useState('')
  const [date, setDate] = useState('')
  const [sortOrder, setSortOrder] = useState('')
  const [dragging, setDragging] = useState(false)
  const [uploading, setUploading] = useState(false)
  const [progress, setProgress] = useState(0)
  const [notice, setNotice] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [avatarPlayerId, setAvatarPlayerId] = useState('')
  const [avatarPhotos, setAvatarPhotos] = useState<Photo[]>([])
  const [selectedAvatarId, setSelectedAvatarId] = useState('')
  const [avatarLoading, setAvatarLoading] = useState(false)
  const [avatarSaving, setAvatarSaving] = useState(false)
  const [avatarNotice, setAvatarNotice] = useState<string | null>(null)
  const [avatarError, setAvatarError] = useState<string | null>(null)
  const [mediaRevision, setMediaRevision] = useState(0)

  useEffect(() => {
    if (!season) {
      setOptions(null)
      return
    }
    const controller = new AbortController()
    mediaData
      .getOptions(season, controller.signal)
      .then(setOptions)
      .catch((requestError: unknown) => {
        if (!controller.signal.aborted) {
          setOptions(null)
          setError(
            requestError instanceof Error
              ? requestError.message
              : '无法读取赛季选项',
          )
        }
      })
    return () => controller.abort()
  }, [season])

  useEffect(() => {
    if (!options?.players.length) {
      setAvatarPlayerId('')
      return
    }
    setAvatarPlayerId((current) =>
      options.players.some((player) => player.id === current)
        ? current
        : options.players[0].id,
    )
  }, [options])

  useEffect(() => {
    if (!season || !avatarPlayerId) {
      setAvatarPhotos([])
      setSelectedAvatarId('')
      return
    }

    const controller = new AbortController()
    setAvatarLoading(true)
    setAvatarError(null)
    mediaData
      .getGallery(
        { season, playerId: avatarPlayerId, category: 'player' },
        controller.signal,
      )
      .then((photos) => {
        setAvatarPhotos(photos)
        const currentAvatarUrl = options?.players.find(
          (player) => player.id === avatarPlayerId,
        )?.photoUrl
        const currentMedia = photos.find((photo) => photo.url === currentAvatarUrl)
        setSelectedAvatarId(currentMedia?.id ?? '')
      })
      .catch((requestError: unknown) => {
        if (!controller.signal.aborted) {
          setAvatarPhotos([])
          setSelectedAvatarId('')
          setAvatarError(
            requestError instanceof Error
              ? requestError.message
              : '无法读取该球员的照片',
          )
        }
      })
      .finally(() => {
        if (!controller.signal.aborted) setAvatarLoading(false)
      })

    return () => controller.abort()
  }, [avatarPlayerId, mediaRevision, options, season])

  function addFiles(fileList: FileList | File[]) {
    const incoming = Array.from(fileList)
    const invalid = incoming.find((file) => !acceptedExtensions.test(file.name))
    if (invalid) {
      setError(`不支持的文件：${invalid.name}`)
      return
    }
    const selected = category === 'team' ? incoming.slice(0, 1) : incoming
    if (category === 'team' && incoming.length > 1) {
      setNotice('队徽每次只上传一张，已保留第一张。')
    } else {
      setNotice(null)
    }
    setError(null)
    setFiles((current) => [
      ...(category === 'team' ? [] : current),
      ...selected.map((file) => ({
        key: `${file.name}-${file.size}-${crypto.randomUUID()}`,
        file,
        previewUrl: URL.createObjectURL(file),
        playerId: '',
      })),
    ])
  }

  function removeFile(key: string) {
    setFiles((current) => {
      const removed = current.find((item) => item.key === key)
      if (removed) URL.revokeObjectURL(removed.previewUrl)
      return current.filter((item) => item.key !== key)
    })
  }

  function clearFiles() {
    files.forEach((item) => URL.revokeObjectURL(item.previewUrl))
    setFiles([])
  }

  function onDrop(event: DragEvent<HTMLDivElement>) {
    event.preventDefault()
    setDragging(false)
    addFiles(event.dataTransfer.files)
  }

  function updatePlayerBinding(key: string, playerId: string) {
    setFiles((current) =>
      current.map((item) => (item.key === key ? { ...item, playerId } : item)),
    )
  }

  async function submitUpload() {
    setError(null)
    setNotice(null)
    if (!files.length) {
      setError('请先选择图片。')
      return
    }
    if (!season) {
      setError('请选择赛季。')
      return
    }
    if (category === 'player' && files.some((item) => !item.playerId)) {
      setError('请为每张球员照片选择对应球员。')
      return
    }
    if (category === 'team' && !teamId) {
      setError('请选择球队。')
      return
    }
    setUploading(true)
    setProgress(0)
    try {
      const uploaded = await mediaData.upload(
        {
          files: files.map((item) => item.file),
          category,
          season: season || undefined,
          playerIds:
            category === 'player'
              ? files.map((item) => item.playerId)
              : [],
          teamId: teamId || undefined,
          title: title || undefined,
          caption: caption || undefined,
          date: date || undefined,
          sortOrder: sortOrder ? Number(sortOrder) : undefined,
        },
        setProgress,
      )
      setProgress(100)
      setNotice(
        category === 'player'
          ? `已成功上传 ${uploaded.length} 张球员照片。头像不会自动变化，请在上方“球员头像设置”中手动选择。`
          : `已成功上传 ${uploaded.length} 张图片。`,
      )
      clearFiles()
      setMediaRevision((current) => current + 1)
    } catch (uploadError) {
      setError(
        uploadError instanceof Error ? uploadError.message : '图片上传失败',
      )
    } finally {
      setUploading(false)
    }
  }

  async function savePlayerAvatar() {
    if (!season || !avatarPlayerId || !selectedAvatarId) {
      setAvatarError('请选择球员和一张照片。')
      return
    }
    setAvatarSaving(true)
    setAvatarError(null)
    setAvatarNotice(null)
    try {
      const result = await mediaData.setPlayerAvatar({
        season,
        playerId: avatarPlayerId,
        mediaId: selectedAvatarId,
      })
      setOptions((current) => current && ({
        ...current,
        players: current.players.map((player) =>
          player.id === result.playerId
            ? { ...player, photoUrl: result.photoUrl }
            : player,
        ),
      }))
      setAvatarNotice('头像已更新。球员列表和球员详情页刷新后会使用这张照片。')
    } catch (saveError) {
      setAvatarError(
        saveError instanceof Error ? saveError.message : '头像更新失败',
      )
    } finally {
      setAvatarSaving(false)
    }
  }

  async function logout() {
    try {
      await adminAuth.logout()
    } finally {
      navigate('/admin/login', { replace: true })
    }
  }

  return (
    <div className="page">
      <section className="content-wrap media-admin">
        <PageHeader
          eyebrow="LOCAL MEDIA ADMIN"
          title="媒体上传"
          description="只按赛季管理球员照片、球队合照和球队队徽。"
          aside={<button className="admin-logout" type="button" onClick={logout}>退出管理</button>}
        />

        <section className="avatar-manager" aria-labelledby="avatar-manager-title">
          <div className="avatar-manager-heading">
            <div>
              <p className="section-kicker">PLAYER AVATAR</p>
              <h2 id="avatar-manager-title">球员头像设置</h2>
              <p>上传照片不会再自动替换头像。请在这里明确选择一张球员照片。</p>
            </div>
            <label>
              <span>Player</span>
              <select
                value={avatarPlayerId}
                onChange={(event) => {
                  setAvatarPlayerId(event.target.value)
                  setAvatarNotice(null)
                  setAvatarError(null)
                }}
              >
                {options?.players.map((player) => (
                  <option key={player.id} value={player.id}>{player.name}</option>
                ))}
              </select>
            </label>
          </div>

          <div className="avatar-manager-body">
            <div className="current-avatar-card">
              <span>当前头像</span>
              {options?.players.find((player) => player.id === avatarPlayerId)?.photoUrl ? (
                <img
                  src={options.players.find((player) => player.id === avatarPlayerId)?.photoUrl ?? ''}
                  alt="当前球员头像"
                />
              ) : (
                <div className="current-avatar-empty">暂无头像</div>
              )}
            </div>

            <div className="avatar-photo-library">
              <strong>该球员已上传的照片</strong>
              {avatarLoading ? (
                <p className="avatar-library-empty">正在加载照片…</p>
              ) : avatarPhotos.length ? (
                <div className="avatar-photo-options">
                  {avatarPhotos.map((photo) => (
                    <button
                      type="button"
                      key={photo.id}
                      className={selectedAvatarId === photo.id ? 'selected' : ''}
                      aria-pressed={selectedAvatarId === photo.id}
                      onClick={() => {
                        setSelectedAvatarId(photo.id)
                        setAvatarNotice(null)
                        setAvatarError(null)
                      }}
                    >
                      <img src={photo.url} alt={photo.originalName} />
                      <span>{selectedAvatarId === photo.id ? '已选择' : '选择'}</span>
                    </button>
                  ))}
                </div>
              ) : (
                <p className="avatar-library-empty">该球员还没有上传照片。</p>
              )}
            </div>
          </div>

          {avatarError && <p className="upload-message error">{avatarError}</p>}
          {avatarNotice && <p className="upload-message success">{avatarNotice}</p>}
          <button
            className="avatar-save-button"
            type="button"
            disabled={avatarSaving || !selectedAvatarId}
            onClick={savePlayerAvatar}
          >
            {avatarSaving ? '保存中…' : '设为头像'}
          </button>
        </section>

        <div className="media-admin-grid">
          <section className="upload-settings">
            <h2>批次信息</h2>
            <div className="upload-form-grid">
              <label>
                <span>Category</span>
                <select
                  value={category}
                  onChange={(event) => {
                    clearFiles()
                    setCategory(event.target.value as MediaCategory)
                    if (!season) setSeason('25-26')
                    setNotice(null)
                    setError(null)
                  }}
                >
                  {categories.map((item) => (
                    <option key={item.value} value={item.value}>{item.label}</option>
                  ))}
                </select>
              </label>

              <label>
                <span>Season</span>
                <select value={season} onChange={(event) => setSeason(event.target.value as Season | '')}>
                  <option value="25-26">25-26</option>
                  <option value="26-27">26-27</option>
                </select>
              </label>

              {category === 'team' && (
                <label>
                  <span>Team</span>
                  <select value={teamId} onChange={(event) => setTeamId(event.target.value)}>
                    <option value="">选择球队</option>
                    {options?.teams.map((team) => <option key={team.id} value={team.id}>{team.name}</option>)}
                  </select>
                </label>
              )}

              {category === 'team_group' && (
                <>
                  <label><span>Title (可选)</span><input value={title} onChange={(event) => setTitle(event.target.value)} /></label>
                  <label><span>Date (可选)</span><input type="date" value={date} onChange={(event) => setDate(event.target.value)} /></label>
                  <label className="wide-field"><span>Caption (可选)</span><input value={caption} onChange={(event) => setCaption(event.target.value)} /></label>
                  <label><span>Sort order (可选)</span><input type="number" value={sortOrder} onChange={(event) => setSortOrder(event.target.value)} /></label>
                </>
              )}

            </div>
          </section>

          <section className="upload-files-panel">
            <div
              className={`upload-dropzone${dragging ? ' is-dragging' : ''}`}
              onDragEnter={(event) => { event.preventDefault(); setDragging(true) }}
              onDragOver={(event) => event.preventDefault()}
              onDragLeave={() => setDragging(false)}
              onDrop={onDrop}
            >
              <strong>拖拽图片到这里</strong>
              <span>或点击选择，支持 JPG / JPEG / PNG / WEBP</span>
              <label className="file-picker">
                选择图片
                <input
                  type="file"
                  accept=".jpg,.jpeg,.png,.webp,image/jpeg,image/png,image/webp"
                  multiple={category !== 'team'}
                  onChange={(event) => event.target.files && addFiles(event.target.files)}
                />
              </label>
            </div>

            {files.length > 0 && (
              <div className="upload-preview-list">
                {files.map((item, index) => (
                  <article className="upload-preview-item" key={item.key}>
                    <img src={item.previewUrl} alt="" />
                    <div>
                      <strong>{index + 1}. {item.file.name}</strong>
                      <small>{(item.file.size / 1024 / 1024).toFixed(2)} MB</small>
                      {category === 'player' && (
                        <select value={item.playerId} onChange={(event) => updatePlayerBinding(item.key, event.target.value)}>
                          <option value="">选择球员</option>
                          {options?.players.map((player) => <option key={player.id} value={player.id}>{player.name}</option>)}
                        </select>
                      )}
                    </div>
                    <button type="button" onClick={() => removeFile(item.key)} aria-label={`移除 ${item.file.name}`}>移除</button>
                  </article>
                ))}
              </div>
            )}

            {uploading && <progress className="upload-progress" value={progress} max="100" />}
            {error && <p className="upload-message error">{error}</p>}
            {notice && <p className="upload-message success">{notice}</p>}
            <button className="upload-submit" type="button" disabled={uploading || !files.length} onClick={submitUpload}>
              {uploading ? `上传中 ${progress}%` : `Upload ${files.length || ''}`}
            </button>
          </section>
        </div>
      </section>
    </div>
  )
}
