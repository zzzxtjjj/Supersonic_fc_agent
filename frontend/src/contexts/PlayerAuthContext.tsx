import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from 'react'
import { ApiError } from '../services/api'
import { playerAuth } from '../services/playerAuth'
import type { PlayerSession } from '../types/rating'

interface PlayerAuthContextValue {
  session: PlayerSession | null
  loading: boolean
  refresh: () => Promise<void>
  logout: () => Promise<void>
}

const PlayerAuthContext = createContext<PlayerAuthContextValue | null>(null)

export function PlayerAuthProvider({ children }: { children: ReactNode }) {
  const [session, setSession] = useState<PlayerSession | null>(null)
  const [loading, setLoading] = useState(true)

  const refresh = useCallback(async () => {
    try {
      setSession(await playerAuth.me())
    } catch (error) {
      if (!(error instanceof ApiError) || error.status !== 401) throw error
      setSession(null)
    }
  }, [])

  useEffect(() => {
    refresh().catch(() => setSession(null)).finally(() => setLoading(false))
  }, [refresh])

  const logout = useCallback(async () => {
    await playerAuth.logout()
    setSession(null)
  }, [])

  const value = useMemo(
    () => ({ session, loading, refresh, logout }),
    [session, loading, refresh, logout],
  )
  return (
    <PlayerAuthContext.Provider value={value}>
      {children}
    </PlayerAuthContext.Provider>
  )
}

export function usePlayerAuth(): PlayerAuthContextValue {
  const value = useContext(PlayerAuthContext)
  if (!value) throw new Error('usePlayerAuth must be used within PlayerAuthProvider')
  return value
}
