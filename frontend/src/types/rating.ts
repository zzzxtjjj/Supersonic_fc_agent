import type { Team } from './index'

export interface CurrentPlayerUser {
  id: string
  playerId: string
  name: string
  photoUrl: string | null
}

export interface PlayerSession {
  authenticated: true
  user: CurrentPlayerUser
  isSupersonicPlayer: boolean
}

export interface ViewerPermissions {
  authenticated: boolean
  isSupersonicPlayer: boolean
  canRate: boolean
  canComment: boolean
  canLike: boolean
}

export interface CommunityAuthor {
  playerId: string
  name: string
  photoUrl: string | null
}

export interface CommunityComment {
  id: string
  author: CommunityAuthor
  content: string
  likeCount: number
  likedByMe: boolean
  createdAt: string
  updatedAt: string
}

export interface RatingReason {
  id: string
  author: CommunityAuthor
  score: number
  reason: string
  likeCount: number
  likedByMe: boolean
  updatedAt: string
}

export interface RatingSummary {
  average: number | null
  count: number
  myScore: number | null
  myReason: string | null
  reasons: RatingReason[]
}

export interface RatingPlayer {
  playerId: string
  name: string
  number: number | null
  photoUrl: string | null
  matchFacts: { goals: number; assists: number }
  rating: RatingSummary
  topComment: CommunityComment | null
  commentCount: number
}

export interface RatingMatchSummary {
  id: string
  seasonId: string
  competition: string
  round: number | null
  date: string | null
  homeTeam: Team
  awayTeam: Team
  homeScore: number
  awayScore: number
}

export interface FanMvp {
  playerId: string
  name: string
  photoUrl: string | null
  average: number
  ratingCount: number
}

export interface RatingMatchResponse {
  match: RatingMatchSummary
  viewer: ViewerPermissions
  fanMvp: FanMvp | null
  players: RatingPlayer[]
}
