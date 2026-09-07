import { Navigate, Route, Routes } from 'react-router-dom'
import { AppShell } from './components/layout/AppShell'
import { RequireAdmin } from './components/admin/RequireAdmin'
import { AgentPage } from './pages/AgentPage'
import { GalleryPage } from './pages/GalleryPage'
import { MatchesPage } from './pages/MatchesPage'
import { AdminLoginPage } from './pages/AdminLoginPage'
import { MediaAdminPage } from './pages/MediaAdminPage'
import { NotFoundPage } from './pages/NotFoundPage'
import { PlayerDetailPage } from './pages/PlayerDetailPage'
import { PlayersPage } from './pages/PlayersPage'
import { StatsPage } from './pages/StatsPage'
import { PlayerLoginPage } from './pages/PlayerLoginPage'
import { PlayerActivatePage } from './pages/PlayerActivatePage'
import { RatingsPage } from './pages/RatingsPage'
import { RatingMatchPage } from './pages/RatingMatchPage'
import { AdminShell } from './components/admin/AdminShell'
import { AdminHomePage } from './pages/AdminHomePage'
import { AdminInvitesPage } from './pages/AdminInvitesPage'
import { AdminMatchesPage } from './pages/AdminMatchesPage'
import { AdminPlayersPage } from './pages/AdminPlayersPage'
import { AdminSeasonsPage } from './pages/AdminSeasonsPage'
import { AdminStatsPage } from './pages/AdminStatsPage'

function ProtectedAdmin({ children }: { children: React.ReactNode }) {
  return <RequireAdmin><AdminShell>{children}</AdminShell></RequireAdmin>
}

export default function App() {
  return (
    <AppShell>
      <Routes>
        <Route path="/" element={<Navigate to="/matches" replace />} />
        <Route path="/ai" element={<AgentPage />} />
        <Route path="/gallery" element={<GalleryPage />} />
        <Route path="/matches" element={<MatchesPage />} />
        <Route path="/admin/login" element={<AdminLoginPage />} />
        <Route path="/admin" element={<ProtectedAdmin><AdminHomePage /></ProtectedAdmin>} />
        <Route path="/admin/media" element={<ProtectedAdmin><MediaAdminPage /></ProtectedAdmin>} />
        <Route path="/admin/seasons" element={<ProtectedAdmin><AdminSeasonsPage /></ProtectedAdmin>} />
        <Route path="/admin/players" element={<ProtectedAdmin><AdminPlayersPage /></ProtectedAdmin>} />
        <Route path="/admin/matches" element={<ProtectedAdmin><AdminMatchesPage /></ProtectedAdmin>} />
        <Route path="/admin/stats" element={<ProtectedAdmin><AdminStatsPage /></ProtectedAdmin>} />
        <Route path="/admin/invites" element={<ProtectedAdmin><AdminInvitesPage /></ProtectedAdmin>} />
        <Route path="/players" element={<PlayersPage />} />
        <Route path="/players/:id" element={<PlayerDetailPage />} />
        <Route path="/stats" element={<StatsPage />} />
        <Route path="/ratings" element={<RatingsPage />} />
        <Route path="/ratings/matches/:matchId" element={<RatingMatchPage />} />
        <Route path="/player/login" element={<PlayerLoginPage />} />
        <Route path="/player/activate" element={<PlayerActivatePage />} />
        <Route path="*" element={<NotFoundPage />} />
      </Routes>
    </AppShell>
  )
}
