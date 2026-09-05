# Supersonic FC API Contract

Base path: `/api`. JSON is used unless stated otherwise. Season display data is
read from `data/seasons/<season>/`; the frontend never reads those files directly.

## Common errors

```json
{ "detail": "Human-readable error message" }
```

- `404`: season, player, or match does not exist.
- `422`: invalid path, query, body, or form data.
- `500`: unexpected server error.

## POST `/api/agent/chat`

The Agent adapter remains intentionally unconnected.

**Request body**

```json
{ "message": "用户问题", "session_id": null }
```

**Query params:** none.

**Future response:** `answer`, `session_id`, `sources`, and optional operational
`tool_trace`. It must never expose reasoning, `reasoning_details`, or API keys.

**Status codes:** `200` future success; `422`; `501` current placeholder; `500`.

## GET `/api/players`

Returns player identity and season data as separate nested objects. Season goals
are derived from match events rather than copied into `players.json`.

**Request:** no body.

**Query params:** `season: string` (required), `status?: string`, `limit?: integer`
(1–100, default 20), `offset?: integer` (minimum 0, default 0).

**Response**

```json
{
  "season": "25-26",
  "items": [
    {
      "player": {
        "id": "player-id",
        "name": "球员姓名",
        "photo_url": null,
        "hometown": null,
        "dominant_foot": null,
        "status": null
      },
      "season": {
        "season": "25-26",
        "number": null,
        "position": null,
        "appearances": null,
        "goals": 0,
        "assists": null,
        "technical_profile": null,
        "scorer_table_eligible": true,
        "scorer_table_exclusion_reason": null
      }
    }
  ],
  "total": 1
}
```

**Status codes:** `200`; `404`; `422`; `500`.

## GET `/api/players/{player_id}`

**Request:** no body. `player_id` is required.

**Query params:** none.

**Response:** `{ "player": Player, "seasons": [PlayerSeason] }` using the same
identity and season structures as the list endpoint.

**Status codes:** `200`; `404`; `500`.

## GET `/api/matches`

**Request:** no body.

**Query params:** `season: string` (required), `stage?: regular | playoff_semifinal`,
`limit?: integer` (1–100, default 20), `offset?: integer` (minimum 0, default 0).

**Response**

```json
{
  "season": "25-26",
  "items": [
    {
      "id": "match-id",
      "season": "25-26",
      "competition": "competition",
      "stage": "regular",
      "round": 1,
      "leg": null,
      "date": null,
      "home_team": {"id": "team-id", "name": "标准队名", "crest_url": null},
      "away_team": {"id": "team-id", "name": "标准队名", "crest_url": null},
      "home_score": 0,
      "away_score": 0,
      "scorers": [
        {
          "type": "player",
          "goals": 1,
          "player_id": "player-id",
          "player_name": "球员姓名",
          "note": null
        }
      ]
    }
  ],
  "total": 1
}
```

`scorers` records only Supersonic goals. `type=own_goal` has no player ID and is
never included in a player's total.

**Status codes:** `200`; `404`; `422`; `500`.

## GET `/api/matches/{match_id}`

**Request:** no body. `match_id` is required.

**Query params:** none.

**Response:** `{ "match": Match }` using the list item structure above.

**Status codes:** `200`; `404`; `500`.

## GET `/api/stats/standings`

**Request:** no body.

**Query params:** `season: string` (required).

**Response:** `{ "season": "25-26", "items": [...] }`. Each item contains only
`rank`, `team_id`, `team_name`, `crest_url`, `points`, `goal_difference`, and
`goals_for`. Wins, draws, losses, matches played, and goals against are not inferred.

**Status codes:** `200`; `404`; `422`; `500`.

## GET `/api/stats/scorers`

Derived on every request from `matches.json` player goal events.

**Request:** no body.

**Query params:** `season: string` (required), `show_all_scorers?: boolean`
(default `false`). When false, players with `scorer_table_eligible=false` are
excluded without deleting their historical goals.

**Response:** season, `show_all_scorers`, and items containing `rank`, `player_id`,
`player_name`, `photo_url`, `goals`, eligibility, and optional exclusion reason.

**Status codes:** `200`; `404`; `422`; `500`.

## GET `/api/stats/assists`

**Request:** no body. **Query params:** required `season`.

No verified assists data source exists, so the endpoint returns an empty `items`
array and does not infer values.

**Status codes:** `200`; `404`; `422`; `500`.

## Admin authentication

### POST `/api/admin/login`

Accepts `{ "username": "...", "password": "..." }`. On success, sets an
HttpOnly, SameSite=Strict administrator session cookie. The cookie is marked
Secure when `APP_ENV=production`.

**Status codes:** `200`; `401`; `503` when backend credentials are not configured.

### GET `/api/admin/me`

Returns `{ "authenticated": true | false }`. It never returns the session token.

### POST `/api/admin/logout`

Invalidates the server-side session and clears the cookie.

## GET `/api/gallery`

Returns persisted local media metadata.

**Request:** no body.

**Query params:** optional `season`, `player_id`, `category`, `limit`, and
`offset`. Media categories are limited to `player`, `team_group`, and `team`.

**Response:** `{ "items": [GalleryItem], "total": 1 }`. Each item includes
`id`, `type`, `url`, `original_name`, optional season/entity bindings, display
metadata, and `created_at`.

**Status codes:** `200`; `422`; `500`.

## GET `/api/gallery/options`

Returns canonical player and team choices for the selected season.

**Request:** no body.

**Query params:** required `season`.

**Response:** `{ "season": "25-26", "players": [], "teams": [] }`.

**Status codes:** `200`; `404`; `422`; `500`.

## POST `/api/gallery/upload`

**Request:** `multipart/form-data` with one or more `files`, required `category`
(`player`, `team_group`, or `team`) and required `season`. Optional fields are
`player_ids` (JSON array), `team_id`, `title`, `caption`, `date`, and
`sort_order`. Player uploads require one player id per file; team-group uploads
support multiple files without match binding; team-crest uploads require one
file and one team.

**Query params:** none.

**Response:** `{ "status": "uploaded", "items": [GalleryItem] }`.

**Status codes:** `201`; `400` invalid image or binding; `422`; `500`.

Requires an authenticated administrator session; otherwise returns `401`, or
`403` for a valid non-admin session.

## PATCH `/api/gallery/{media_id}`

Updates administrator-managed display metadata (`title`, `caption`, `date`, or
`sort_order`). Requires an administrator session.

**Status codes:** `200`; `401`; `403`; `404`; `422`.

## DELETE `/api/gallery/{media_id}`

Deletes the stored media file and metadata. If the deleted item is the currently
bound player photo or team crest, that binding is cleared. Requires an
administrator session.

**Status codes:** `200`; `401`; `403`; `404`.
