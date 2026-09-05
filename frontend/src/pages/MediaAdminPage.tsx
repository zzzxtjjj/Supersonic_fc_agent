import { useEffect, useState, type DragEvent } from 'react'
import { useNavigate } from 'react-router-dom'
import { PageHeader } from '../components/layout/PageHeader'
import { adminAuth } from '../services/adminAuth'
import { mediaData } from '../services/mediaData'
import type {
  MediaCategory,
  MediaOptions,
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
      setNotice(`已成功上传 ${uploaded.length} 张图片。`)
      clearFiles()
    } catch (uploadError) {
      setError(
        uploadError instanceof Error ? uploadError.message : '图片上传失败',
      )
    } finally {
      setUploading(false)
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
