import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'
import './App.css'
import AppShell from './components/layout/AppShell'
import PersonCreatePage from './pages/PersonCreatePage'
import PersonEditPage from './pages/PersonEditPage'
import PersonProfilePage from './pages/PersonProfilePage'
import PeoplePage from './pages/PeoplePage'

function App() {
  return (
    <BrowserRouter>
      <AppShell>
        <Routes>
          <Route path="/" element={<Navigate to="/pessoas" replace />} />
          <Route path="/pessoas" element={<PeoplePage />} />
          <Route path="/pessoas/nova" element={<PersonCreatePage />} />
          <Route path="/pessoas/:id/editar" element={<PersonEditPage />} />
          <Route path="/pessoas/:id" element={<PersonProfilePage />} />
          <Route path="*" element={<Navigate to="/pessoas" replace />} />
        </Routes>
      </AppShell>
    </BrowserRouter>
  )
}

export default App
