import type {
  MediaCategory,
  MediaOptions,
  Photo,
  Season,
} from '../types'
import { apiRequest, resolveMediaUrl, uploadFormData } from './api'

interface ApiMediaItem {
  id: string
  type: MediaCategory
  url: string
  original_name: string
  season: Season | null
  player_ids: string[]
  team_id: string | null
  title: string | null
  caption: string | null
  date: string | null
  sort_order: number | null
  created_at: string
}

interface ApiMediaOptions {
  season: Season
  players: { id: string; name: string }[]
  teams: { id: string; name: string }[]
}

export interface MediaUploadInput {
  files: File[]
  category: MediaCategory
  season?: Season
  playerIds?: string[]
  teamId?: string
  title?: string
  caption?: string
  date?: string
  sortOrder?: number
}

function mapMediaItem(item: ApiMediaItem): Photo {
  return {
    id: item.id,
    type: item.type,
    url: resolveMediaUrl(item.url) ?? item.url,
    originalName: item.original_name,
    season: item.season,
    playerIds: item.player_ids,
    teamId: item.team_id,
    title: item.title,
    caption: item.caption,
    date: item.date,
    sortOrder: item.sort_order,
    createdAt: item.created_at,
  }
}

export const mediaData = {
  async getGallery(
    filters: {
      season?: Season
      playerId?: string
      category?: MediaCategory
    } = {},
    signal?: AbortSignal,
  ): Promise<Photo[]> {
    const params = new URLSearchParams()
    if (filters.season) params.set('season', filters.season)
    if (filters.playerId) params.set('player_id', filters.playerId)
    if (filters.category) params.set('category', filters.category)
    const query = params.size ? `?${params.toString()}` : ''
    const response = await apiRequest<{ items: ApiMediaItem[] }>(`/gallery${query}`, {
      signal,
    })
    return response.items.map(mapMediaItem)
  },

  async getOptions(season: Season, signal?: AbortSignal): Promise<MediaOptions> {
    const response = await apiRequest<ApiMediaOptions>(
      `/gallery/options?season=${encodeURIComponent(season)}`,
      { signal },
    )
    return response
  },

  async upload(
    input: MediaUploadInput,
    onProgress?: (percent: number) => void,
  ): Promise<Photo[]> {
    const formData = new FormData()
    input.files.forEach((file) => formData.append('files', file))
    formData.append('category', input.category)
    if (input.season) formData.append('season', input.season)
    if (input.playerIds?.length) {
      formData.append('player_ids', JSON.stringify(input.playerIds))
    }
    if (input.teamId) formData.append('team_id', input.teamId)
    if (input.title) formData.append('title', input.title)
    if (input.caption) formData.append('caption', input.caption)
    if (input.date) formData.append('date', input.date)
    if (input.sortOrder !== undefined) {
      formData.append('sort_order', String(input.sortOrder))
    }

    const response = await uploadFormData<{
      status: string
      items: ApiMediaItem[]
    }>('/gallery/upload', formData, onProgress)
    return response.items.map(mapMediaItem)
  },
}
