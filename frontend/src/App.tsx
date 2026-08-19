import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'
import './App.css'
import AppShell from './components/layout/AppShell'
import AccessRequestPage from './pages/AccessRequestPage'
import AccessRequestDetailPage from './pages/AccessRequestDetailPage'
import AccessRequestsPage from './pages/AccessRequestsPage'
import ActivateAccountPage from './pages/ActivateAccountPage'
import LoginPage from './pages/LoginPage'
import PersonCreatePage from './pages/PersonCreatePage'
import PersonEditPage from './pages/PersonEditPage'
import PersonProfilePage from './pages/PersonProfilePage'
import PeoplePage from './pages/PeoplePage'
import UserAccessPage from './pages/UserAccessPage'
import UsersPage from './pages/UsersPage'
import { useCurrentUser } from './hooks/useAuth'

function AdminRoutes() {
  const { data: currentUser, isError, isLoading } = useCurrentUser()

  if (isLoading) {
    return (
      <main className="public-access-page">
        <section className="access-request-shell auth-shell">
          <div className="access-request-heading">
            <h1>Carregando sessao...</h1>
            <p>Aguarde enquanto verificamos seu acesso.</p>
          </div>
        </section>
      </main>
    )
  }

  if (isError || !currentUser?.is_authenticated) {
    const next = encodeURIComponent(window.location.pathname + window.location.search)
    return <Navigate to={`/login?next=${next}`} replace />
  }

  return (
    <AppShell>
      <Routes>
        <Route path="/" element={<Navigate to="/pessoas" replace />} />
        <Route path="/pessoas" element={<PeoplePage />} />
        <Route path="/pessoas/nova" element={<PersonCreatePage />} />
        <Route path="/pessoas/:id/acesso" element={<UserAccessPage />} />
        <Route path="/pessoas/:id/editar" element={<PersonEditPage />} />
        <Route path="/pessoas/:id" element={<PersonProfilePage />} />
        <Route path="/solicitacoes-acesso" element={<AccessRequestsPage />} />
        <Route path="/solicitacoes-acesso/:id" element={<AccessRequestDetailPage />} />
        <Route path="/usuarios" element={<UsersPage />} />
        <Route path="*" element={<Navigate to="/pessoas" replace />} />
      </Routes>
    </AppShell>
  )
}

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route path="/pedir-acesso" element={<AccessRequestPage />} />
        <Route path="/ativar-conta/:uid/:token" element={<ActivateAccountPage />} />
        <Route path="/*" element={<AdminRoutes />} />
      </Routes>
    </BrowserRouter>
  )
}

export default App
