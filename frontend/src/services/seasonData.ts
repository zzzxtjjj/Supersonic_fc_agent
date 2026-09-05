import type {
  Match,
  Player,
  PlayerDetail,
  PlayerListItem,
  PlayerSeason,
  RankingEntry,
  ScorerEvent,
  Season,
  Standing,
  Team,
} from '../types'
import { apiRequest, resolveMediaUrl } from './api'

interface ApiTeam {
  id: string
  name: string
  crest_url: string | null
}

interface ApiScorerEvent {
  type: 'player' | 'own_goal'
  goals: number
  player_id: string | null
  player_name: string | null
  note: string | null
}

interface ApiMatch {
  id: string
  season: Season
  competition: string
  stage: 'regular' | 'playoff_semifinal'
  round: number | null
  leg: number | null
  date: string | null
  home_team: ApiTeam
  away_team: ApiTeam
  home_score: number
  away_score: number
  scorers: ApiScorerEvent[]
}

interface ApiPlayer {
  id: string
  name: string
  photo_url: string | null
  hometown: string | null
  dominant_foot: string | null
  status: 'active' | 'inactive' | null
  profile_complete: boolean
}

interface ApiPlayerSeason {
  season: Season
  number: number | null
  position: string | null
  appearances: number | null
  goals: number | null
  assists: number | null
  technical_profile: string | null
  is_captain: boolean
  scorer_table_eligible: boolean
  scorer_table_exclusion_reason: string | null
}

interface ApiPlayerListItem {
  player: ApiPlayer
  season: ApiPlayerSeason
}

interface ApiStanding {
  rank: number
  team_id: string
  team_name: string
  crest_url: string | null
  points: number
  goal_difference: number
  goals_for: number
}

interface ApiScorer {
  rank: number
  player_id: string
  player_name: string
  photo_url: string | null
  goals: number
}

function mapTeam(team: ApiTeam): Team {
  return { id: team.id, name: team.name, crestUrl: resolveMediaUrl(team.crest_url) }
}

function mapScorer(scorer: ApiScorerEvent): ScorerEvent {
  return {
    type: scorer.type,
    goals: scorer.goals,
    playerId: scorer.player_id,
    playerName: scorer.player_name,
    note: scorer.note,
  }
}

function mapMatch(match: ApiMatch): Match {
  return {
    id: match.id,
    season: match.season,
    competition: match.competition,
    stage: match.stage,
    round: match.round,
    leg: match.leg,
    date: match.date,
    homeTeam: mapTeam(match.home_team),
    awayTeam: mapTeam(match.away_team),
    homeScore: match.home_score,
    awayScore: match.away_score,
    scorers: match.scorers.map(mapScorer),
  }
}

function mapPlayer(player: ApiPlayer): Player {
  return {
    id: player.id,
    name: player.name,
    photoUrl: resolveMediaUrl(player.photo_url),
    hometown: player.hometown,
    dominantFoot: player.dominant_foot,
    status: player.status,
    profileComplete: player.profile_complete,
  }
}

function mapPlayerSeason(season: ApiPlayerSeason): PlayerSeason {
  return {
    season: season.season,
    number: season.number,
    position: season.position,
    appearances: season.appearances,
    goals: season.goals,
    assists: season.assists,
    technicalProfile: season.technical_profile,
    isCaptain: season.is_captain,
    scorerTableEligible: season.scorer_table_eligible,
    scorerTableExclusionReason: season.scorer_table_exclusion_reason,
  }
}

export const seasonData = {
  async getMatches(season: Season, signal?: AbortSignal): Promise<Match[]> {
    const response = await apiRequest<{ items: ApiMatch[] }>(
      `/matches?season=${encodeURIComponent(season)}`,
      { signal },
    )
    return response.items.map(mapMatch)
  },

  async getPlayers(
    season: Season,
    signal?: AbortSignal,
  ): Promise<PlayerListItem[]> {
    const response = await apiRequest<{ items: ApiPlayerListItem[] }>(
      `/players?season=${encodeURIComponent(season)}`,
      { signal },
    )
    return response.items.map((item) => ({
      player: mapPlayer(item.player),
      season: mapPlayerSeason(item.season),
    }))
  },

  async getPlayer(playerId: string, signal?: AbortSignal): Promise<PlayerDetail> {
    const response = await apiRequest<{
      player: ApiPlayer
      seasons: ApiPlayerSeason[]
    }>(`/players/${encodeURIComponent(playerId)}`, { signal })
    return {
      player: mapPlayer(response.player),
      seasons: response.seasons.map(mapPlayerSeason),
    }
  },

  async getStandings(season: Season, signal?: AbortSignal): Promise<Standing[]> {
    const response = await apiRequest<{ items: ApiStanding[] }>(
      `/stats/standings?season=${encodeURIComponent(season)}`,
      { signal },
    )
    return response.items.map((row) => ({
      rank: row.rank,
      teamId: row.team_id,
      teamName: row.team_name,
      crestUrl: resolveMediaUrl(row.crest_url),
      points: row.points,
      goalDifference: row.goal_difference,
      goalsFor: row.goals_for,
    }))
  },

  async getScorers(season: Season, signal?: AbortSignal): Promise<RankingEntry[]> {
    const response = await apiRequest<{ items: ApiScorer[] }>(
      `/stats/scorers?season=${encodeURIComponent(season)}`,
      { signal },
    )
    return response.items.map((entry) => ({
      rank: entry.rank,
      playerId: entry.player_id,
      playerName: entry.player_name,
      photoUrl: resolveMediaUrl(entry.photo_url),
      value: entry.goals,
    }))
  },
}
