import type {
  CommunityAuthor,
  CommunityComment,
  RatingMatchResponse,
  RatingPlayer,
  RatingReason,
} from '../types/rating'
import { apiRequest, resolveMediaUrl } from './api'

interface ApiAuthor {
  player_id: string
  name: string
  photo_url: string | null
}

interface ApiComment {
  id: string
  author: ApiAuthor
  content: string
  like_count: number
  liked_by_me: boolean
  created_at: string
  updated_at: string
}

interface ApiRatingReason {
  id: string
  author: ApiAuthor
  score: number
  reason: string
  like_count: number
  liked_by_me: boolean
  updated_at: string
}

interface ApiRatingMatchResponse {
  match: {
    id: string
    season_id: string
    competition: string
    round: number | null
    date: string | null
    home_team: { id: string; name: string; crest_url: string | null }
    away_team: { id: string; name: string; crest_url: string | null }
    home_score: number
    away_score: number
  }
  viewer: {
    authenticated: boolean
    is_supersonic_player: boolean
    can_rate: boolean
    can_comment: boolean
    can_like: boolean
  }
  fan_mvp: {
    player_id: string
    name: string
    photo_url: string | null
    average: number
    rating_count: number
  } | null
  players: Array<{
    player_id: string
    name: string
    number: number | null
    photo_url: string | null
    match_facts: { goals: number; assists: number }
    rating: {
      average: number | null
      count: number
      my_score: number | null
      my_reason: string | null
      reasons: ApiRatingReason[]
    }
    top_comment: ApiComment | null
    comment_count: number
  }>
}

function mapAuthor(author: ApiAuthor): CommunityAuthor {
  return {
    playerId: author.player_id,
    name: author.name,
    photoUrl: resolveMediaUrl(author.photo_url),
  }
}

function mapComment(comment: ApiComment): CommunityComment {
  return {
    id: comment.id,
    author: mapAuthor(comment.author),
    content: comment.content,
    likeCount: comment.like_count,
    likedByMe: comment.liked_by_me,
    createdAt: comment.created_at,
    updatedAt: comment.updated_at,
  }
}

function mapReason(reason: ApiRatingReason): RatingReason {
  return {
    id: reason.id,
    author: mapAuthor(reason.author),
    score: reason.score,
    reason: reason.reason,
    likeCount: reason.like_count,
    likedByMe: reason.liked_by_me,
    updatedAt: reason.updated_at,
  }
}

function mapPlayer(player: ApiRatingMatchResponse['players'][number]): RatingPlayer {
  return {
    playerId: player.player_id,
    name: player.name,
    number: player.number,
    photoUrl: resolveMediaUrl(player.photo_url),
    matchFacts: player.match_facts,
    rating: {
      average: player.rating.average,
      count: player.rating.count,
      myScore: player.rating.my_score,
      myReason: player.rating.my_reason,
      reasons: player.rating.reasons.map(mapReason),
    },
    topComment: player.top_comment ? mapComment(player.top_comment) : null,
    commentCount: player.comment_count,
  }
}

function mapResponse(response: ApiRatingMatchResponse): RatingMatchResponse {
  return {
    match: {
      id: response.match.id,
      seasonId: response.match.season_id,
      competition: response.match.competition,
      round: response.match.round,
      date: response.match.date,
      homeTeam: {
        id: response.match.home_team.id,
        name: response.match.home_team.name,
        crestUrl: resolveMediaUrl(response.match.home_team.crest_url),
      },
      awayTeam: {
        id: response.match.away_team.id,
        name: response.match.away_team.name,
        crestUrl: resolveMediaUrl(response.match.away_team.crest_url),
      },
      homeScore: response.match.home_score,
      awayScore: response.match.away_score,
    },
    viewer: {
      authenticated: response.viewer.authenticated,
      isSupersonicPlayer: response.viewer.is_supersonic_player,
      canRate: response.viewer.can_rate,
      canComment: response.viewer.can_comment,
      canLike: response.viewer.can_like,
    },
    fanMvp: response.fan_mvp
      ? {
          playerId: response.fan_mvp.player_id,
          name: response.fan_mvp.name,
          photoUrl: resolveMediaUrl(response.fan_mvp.photo_url),
          average: response.fan_mvp.average,
          ratingCount: response.fan_mvp.rating_count,
        }
      : null,
    players: response.players.map(mapPlayer),
  }
}

export const ratingData = {
  async getMatch(matchId: string, signal?: AbortSignal): Promise<RatingMatchResponse> {
    return mapResponse(
      await apiRequest<ApiRatingMatchResponse>(
        `/ratings/matches/${encodeURIComponent(matchId)}`,
        { signal },
      ),
    )
  },

  submitRating(matchId: string, playerId: string, score: number) {
    return apiRequest<{
      rating_id: string
      score: number
      reason: string | null
      average: number
      rating_count: number
    }>(
      `/ratings/matches/${encodeURIComponent(matchId)}/players/${encodeURIComponent(playerId)}`,
      {
        method: 'PUT',
        body: JSON.stringify({ score, reason: null }),
      },
    )
  },

  async getComments(matchId: string, playerId: string): Promise<CommunityComment[]> {
    const response = await apiRequest<{ comments: ApiComment[] }>(
      `/ratings/matches/${encodeURIComponent(matchId)}/players/${encodeURIComponent(playerId)}/comments`,
    )
    return response.comments.map(mapComment)
  },

  async createComment(matchId: string, playerId: string, content: string) {
    return mapComment(
      await apiRequest<ApiComment>(
        `/ratings/matches/${encodeURIComponent(matchId)}/players/${encodeURIComponent(playerId)}/comments`,
        { method: 'POST', body: JSON.stringify({ content }) },
      ),
    )
  },

  likeRating(ratingId: string) {
    return apiRequest<{ liked: boolean; like_count: number }>(
      `/ratings/${encodeURIComponent(ratingId)}/like`,
      { method: 'POST' },
    )
  },

  likeComment(commentId: string) {
    return apiRequest<{ liked: boolean; like_count: number }>(
      `/comments/${encodeURIComponent(commentId)}/like`,
      { method: 'POST' },
    )
  },
}
