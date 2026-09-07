import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import App from './App'
import { PlayerAuthProvider } from './contexts/PlayerAuthContext'
import './styles.css'
import './rating-admin.css'

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <BrowserRouter>
      <PlayerAuthProvider>
        <App />
      </PlayerAuthProvider>
    </BrowserRouter>
  </StrictMode>,
)
