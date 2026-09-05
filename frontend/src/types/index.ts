export type Season = '25-26' | '26-27'

export type PlayerStatus = 'active' | 'inactive' | null

export interface Player {
  id: string
  name: string
  photoUrl: string | null
  hometown: string | null
  dominantFoot: string | null
  status: PlayerStatus
  profileComplete: boolean
}

export interface PlayerSeason {
  season: Season
  number: number | null
  position: string | null
  appearances: number | null
  goals: number | null
  assists: number | null
  technicalProfile: string | null
  isCaptain: boolean
  scorerTableEligible: boolean
  scorerTableExclusionReason: string | null
}

export interface PlayerListItem {
  player: Player
  season: PlayerSeason
}

export interface PlayerDetail {
  player: Player
  seasons: PlayerSeason[]
}

export interface Team {
  id: string
  name: string
  crestUrl: string | null
}

export interface ScorerEvent {
  type: 'player' | 'own_goal'
  goals: number
  playerId: string | null
  playerName: string | null
  note: string | null
}

export interface Match {
  id: string
  season: Season
  competition: string
  stage: 'regular' | 'playoff_semifinal'
  date: string | null
  round: number | null
  leg: number | null
  homeTeam: Team
  awayTeam: Team
  homeScore: number
  awayScore: number
  scorers: ScorerEvent[]
}

export type MediaCategory = 'player' | 'team_group' | 'team'

export interface Photo {
  id: string
  url: string
  type: MediaCategory
  originalName: string
  season: Season | null
  playerIds: string[]
  teamId: string | null
  title: string | null
  caption: string | null
  date: string | null
  sortOrder: number | null
  createdAt: string
}

export interface MediaOption {
  id: string
  name: string
}

export interface MediaPlayerOption extends MediaOption {
  photoUrl: string | null
}

export interface MediaOptions {
  season: Season
  players: MediaPlayerOption[]
  teams: MediaOption[]
}

export interface Standing {
  rank: number
  teamId: string
  teamName: string
  crestUrl: string | null
  points: number
  goalDifference: number
  goalsFor: number
}

export interface RankingEntry {
  rank: number
  playerId: string
  playerName: string
  photoUrl: string | null
  value: number
}
