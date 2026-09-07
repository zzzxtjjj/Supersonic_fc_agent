import type {
  AdminMatch,
  AdminPlayer,
  AdminStatsPreview,
} from '../types/admin'
import { apiRequest } from './api'

export const adminData = {
  async getSeasons(signal?: AbortSignal): Promise<string[]> {
    const response = await apiRequest<{ seasons: string[] }>('/admin/seasons', { signal })
    return response.seasons
  },

  createSeason(
    seasonId: string,
    teams: Array<{ id: string; name: string; aliases: string[]; crest_url: string | null }> = [],
  ) {
    return apiRequest<{ season_id: string; created_files: string[] }>('/admin/seasons', {
      method: 'POST',
      body: JSON.stringify({ season_id: seasonId, teams }),
    })
  },

  async getPlayers(seasonId: string, signal?: AbortSignal): Promise<AdminPlayer[]> {
    const response = await apiRequest<{ players: AdminPlayer[] }>(
      `/admin/seasons/${encodeURIComponent(seasonId)}/players`,
      { signal },
    )
    return response.players
  },

  createPlayer(seasonId: string, player: AdminPlayer) {
    return apiRequest<AdminPlayer>(
      `/admin/seasons/${encodeURIComponent(seasonId)}/players`,
      { method: 'POST', body: JSON.stringify(player) },
    )
  },

  updatePlayer(seasonId: string, playerId: string, changes: Partial<AdminPlayer>) {
    return apiRequest<AdminPlayer>(
      `/admin/seasons/${encodeURIComponent(seasonId)}/players/${encodeURIComponent(playerId)}`,
      { method: 'PATCH', body: JSON.stringify(changes) },
    )
  },

  async getMatches(seasonId: string, signal?: AbortSignal): Promise<AdminMatch[]> {
    const response = await apiRequest<{ matches: AdminMatch[] }>(
      `/admin/seasons/${encodeURIComponent(seasonId)}/matches`,
      { signal },
    )
    return response.matches
  },

  createMatch(seasonId: string, match: AdminMatch) {
    return apiRequest<AdminMatch>(
      `/admin/seasons/${encodeURIComponent(seasonId)}/matches`,
      { method: 'POST', body: JSON.stringify(match) },
    )
  },

  updateMatch(seasonId: string, match: AdminMatch) {
    return apiRequest<AdminMatch>(
      `/admin/seasons/${encodeURIComponent(seasonId)}/matches/${encodeURIComponent(match.id)}`,
      { method: 'PUT', body: JSON.stringify(match) },
    )
  },

  async getStatsPreview(seasonId: string, signal?: AbortSignal): Promise<AdminStatsPreview> {
    const response = await apiRequest<{
      season_id: string
      scorers: Array<{ player_id: string; name: string; goals: number | null; assists: number | null }>
      assists: Array<{ player_id: string; name: string; goals: number | null; assists: number | null }>
    }>(`/admin/seasons/${encodeURIComponent(seasonId)}/stats-preview`, { signal })
    const mapEntry = (entry: (typeof response.scorers)[number]) => ({
      playerId: entry.player_id,
      name: entry.name,
      goals: entry.goals,
      assists: entry.assists,
    })
    return {
      seasonId: response.season_id,
      scorers: response.scorers.map(mapEntry),
      assists: response.assists.map(mapEntry),
    }
  },

  createInvite(playerId: string) {
    return apiRequest<{ player_id: string; invite_code: string; expires_at: string }>(
      `/admin/player-invites/${encodeURIComponent(playerId)}`,
      { method: 'POST' },
    )
  },
}
