import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'
import './App.css'
import AppShell from './components/layout/AppShell'
import AccessRequestPage from './pages/AccessRequestPage'
import AccessRequestDetailPage from './pages/AccessRequestDetailPage'
import AccessRequestsPage from './pages/AccessRequestsPage'
import PersonCreatePage from './pages/PersonCreatePage'
import PersonEditPage from './pages/PersonEditPage'
import PersonProfilePage from './pages/PersonProfilePage'
import PeoplePage from './pages/PeoplePage'

function AdminRoutes() {
  return (
    <AppShell>
      <Routes>
        <Route path="/" element={<Navigate to="/pessoas" replace />} />
        <Route path="/pessoas" element={<PeoplePage />} />
        <Route path="/pessoas/nova" element={<PersonCreatePage />} />
        <Route path="/pessoas/:id/editar" element={<PersonEditPage />} />
        <Route path="/pessoas/:id" element={<PersonProfilePage />} />
        <Route path="/solicitacoes-acesso" element={<AccessRequestsPage />} />
        <Route path="/solicitacoes-acesso/:id" element={<AccessRequestDetailPage />} />
        <Route path="*" element={<Navigate to="/pessoas" replace />} />
      </Routes>
    </AppShell>
  )
}

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/pedir-acesso" element={<AccessRequestPage />} />
        <Route path="/*" element={<AdminRoutes />} />
      </Routes>
    </BrowserRouter>
  )
}

export default App
