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

export default function App() {
  return (
    <AppShell>
      <Routes>
        <Route path="/" element={<Navigate to="/ai" replace />} />
        <Route path="/ai" element={<AgentPage />} />
        <Route path="/gallery" element={<GalleryPage />} />
        <Route path="/matches" element={<MatchesPage />} />
        <Route path="/admin/login" element={<AdminLoginPage />} />
        <Route
          path="/admin/media"
          element={
            <RequireAdmin>
              <MediaAdminPage />
            </RequireAdmin>
          }
        />
        <Route path="/players" element={<PlayersPage />} />
        <Route path="/players/:id" element={<PlayerDetailPage />} />
        <Route path="/stats" element={<StatsPage />} />
        <Route path="*" element={<NotFoundPage />} />
      </Routes>
    </AppShell>
  )
}
