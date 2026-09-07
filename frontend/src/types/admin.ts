export interface AdminPlayer {
  id: string
  name: string
  aliases?: string[] | null
  photo_url?: string | null
  season_data?: {
    number?: number | null
    position?: string | null
    [key: string]: unknown
  } | null
  departure?: Record<string, unknown> | null
  transfers?: Record<string, unknown>[] | null
  career_milestones?: Record<string, unknown>[] | null
  [key: string]: unknown
}

export type AdminMatchEventType =
  | 'goal'
  | 'own_goal'
  | 'substitution'
  | 'yellow_card'
  | 'red_card'

export interface AdminMatchEvent {
  type: AdminMatchEventType
  team_id?: string | null
  player_id?: string | null
  scorer_player_id?: string | null
  assist_player_id?: string | null
  forced_by_player_id?: string | null
  player_in_id?: string | null
  player_out_id?: string | null
  minute?: number | null
  note?: string | null
  [key: string]: unknown
}

export interface AdminMatch {
  id: string
  season?: string | null
  competition: string
  stage: string
  round?: number | null
  leg?: number | null
  date?: string | null
  home_team_id: string
  away_team_id: string
  home_score: number
  away_score: number
  captain_player_id?: string | null
  goalkeeper_player_id?: string | null
  events?: AdminMatchEvent[] | null
  [key: string]: unknown
}

export interface AdminStatsEntry {
  playerId: string
  name: string
  goals: number | null
  assists: number | null
}

export interface AdminStatsPreview {
  seasonId: string
  scorers: AdminStatsEntry[]
  assists: AdminStatsEntry[]
}
