import type { PlayerSession } from '../types/rating'
import { apiRequest, resolveMediaUrl } from './api'

interface ApiMeResponse {
  authenticated: true
  user: {
    id: string
    player_id: string
    name: string
    photo_url: string | null
  }
  is_supersonic_player: boolean
}

function mapSession(response: ApiMeResponse): PlayerSession {
  return {
    authenticated: true,
    user: {
      id: response.user.id,
      playerId: response.user.player_id,
      name: response.user.name,
      photoUrl: resolveMediaUrl(response.user.photo_url),
    },
    isSupersonicPlayer: response.is_supersonic_player,
  }
}

export const playerAuth = {
  async me(signal?: AbortSignal): Promise<PlayerSession> {
    return mapSession(
      await apiRequest<ApiMeResponse>('/player-auth/me', { signal }),
    )
  },

  login(playerId: string, password: string) {
    return apiRequest<{ authenticated: boolean }>('/player-auth/login', {
      method: 'POST',
      body: JSON.stringify({ player_id: playerId, password }),
    })
  },

  activate(inviteCode: string, password: string) {
    return apiRequest<{ activated: boolean }>('/player-auth/activate', {
      method: 'POST',
      body: JSON.stringify({ invite_code: inviteCode, password }),
    })
  },

  logout() {
    return apiRequest<{ authenticated: boolean }>('/player-auth/logout', {
      method: 'POST',
    })
  },
}
