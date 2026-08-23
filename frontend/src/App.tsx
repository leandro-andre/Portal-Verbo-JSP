import { BrowserRouter, Navigate, Route, Routes, useParams } from 'react-router-dom'
import type { ReactNode } from 'react'
import './App.css'
import AppShell from './components/layout/AppShell'
import AccessRequestPage from './pages/AccessRequestPage'
import AccessRequestDetailPage from './pages/AccessRequestDetailPage'
import AccessRequestsPage from './pages/AccessRequestsPage'
import ActivateAccountPage from './pages/ActivateAccountPage'
import DepartmentCreatePage from './pages/DepartmentCreatePage'
import DepartmentDetailPage from './pages/DepartmentDetailPage'
import DepartmentEditPage from './pages/DepartmentEditPage'
import DepartmentsPage from './pages/DepartmentsPage'
import DiscipleshipClassCreatePage from './pages/DiscipleshipClassCreatePage'
import DiscipleshipClassDetailPage from './pages/DiscipleshipClassDetailPage'
import DiscipleshipClassEditPage from './pages/DiscipleshipClassEditPage'
import DiscipleshipClassesPage from './pages/DiscipleshipClassesPage'
import DiscipleshipAttendancePage from './pages/DiscipleshipAttendancePage'
import LoginPage from './pages/LoginPage'
import MembershipPage from './pages/MembershipPage'
import PersonCreatePage from './pages/PersonCreatePage'
import PersonEditPage from './pages/PersonEditPage'
import PersonProfilePage from './pages/PersonProfilePage'
import PeoplePage from './pages/PeoplePage'
import UserAccessPage from './pages/UserAccessPage'
import UsersPage from './pages/UsersPage'
import { useCurrentUser } from './hooks/useAuth'
import { usePerson } from './hooks/usePeople'
import type { Capability } from './types/auth'

function AccessDenied() {
  return (
    <section className="person-profile-page">
      <div className="state-panel state-panel--error">
        <h1>Acesso negado</h1>
        <p>Sua sessao atual nao possui permissao para acessar esta area.</p>
      </div>
    </section>
  )
}

function AuthorizedRoute({
  capability,
  children,
}: {
  capability: Capability
  children: ReactNode
}) {
  const { data: currentUser } = useCurrentUser()
  const canAccess = Boolean(currentUser?.user?.capabilities.includes(capability))
  return canAccess ? children : <AccessDenied />
}

function PersonAccessRedirect() {
  const { id } = useParams()
  const personId = Number(id)
  const { data: person, isError, isLoading } = usePerson(personId)

  if (isLoading) {
    return (
      <section className="person-profile-page">
        <div className="state-panel">
          <h1>Carregando acesso...</h1>
          <p>Aguarde enquanto localizamos o usuario vinculado.</p>
        </div>
      </section>
    )
  }

  if (isError || !person?.portal_user) {
    return <Navigate to="/usuarios" replace />
  }

  return <Navigate to={`/usuarios/${person.portal_user.id}`} replace />
}

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
        <Route path="/pessoas" element={<AuthorizedRoute capability="PEOPLE_VIEW"><PeoplePage /></AuthorizedRoute>} />
        <Route path="/pessoas/nova" element={<AuthorizedRoute capability="PEOPLE_CREATE"><PersonCreatePage /></AuthorizedRoute>} />
        <Route path="/pessoas/:id/acesso" element={<AuthorizedRoute capability="USER_VIEW"><PersonAccessRedirect /></AuthorizedRoute>} />
        <Route path="/pessoas/:id/editar" element={<AuthorizedRoute capability="PEOPLE_CHANGE"><PersonEditPage /></AuthorizedRoute>} />
        <Route path="/pessoas/:id" element={<AuthorizedRoute capability="PEOPLE_VIEW"><PersonProfilePage /></AuthorizedRoute>} />
        <Route path="/solicitacoes-acesso" element={<AuthorizedRoute capability="ACCESS_REQUEST_VIEW"><AccessRequestsPage /></AuthorizedRoute>} />
        <Route path="/solicitacoes-acesso/:id" element={<AuthorizedRoute capability="ACCESS_REQUEST_VIEW"><AccessRequestDetailPage /></AuthorizedRoute>} />
        <Route path="/usuarios" element={<AuthorizedRoute capability="USER_VIEW"><UsersPage /></AuthorizedRoute>} />
        <Route path="/usuarios/:id" element={<AuthorizedRoute capability="USER_VIEW"><UserAccessPage /></AuthorizedRoute>} />
        <Route path="/discipulado" element={<AuthorizedRoute capability="DISCIPLESHIP_CLASS_VIEW"><DiscipleshipClassesPage /></AuthorizedRoute>} />
        <Route path="/membresia" element={<AuthorizedRoute capability="MEMBERSHIP_VIEW"><MembershipPage /></AuthorizedRoute>} />
        <Route path="/departamentos" element={<AuthorizedRoute capability="DEPARTMENT_VIEW"><DepartmentsPage /></AuthorizedRoute>} />
        <Route path="/departamentos/novo" element={<AuthorizedRoute capability="DEPARTMENT_CREATE"><DepartmentCreatePage /></AuthorizedRoute>} />
        <Route path="/departamentos/:id/editar" element={<AuthorizedRoute capability="DEPARTMENT_CHANGE"><DepartmentEditPage /></AuthorizedRoute>} />
        <Route path="/departamentos/:id" element={<AuthorizedRoute capability="DEPARTMENT_VIEW"><DepartmentDetailPage /></AuthorizedRoute>} />
        <Route path="/discipulado/nova" element={<AuthorizedRoute capability="DISCIPLESHIP_CLASS_CREATE"><DiscipleshipClassCreatePage /></AuthorizedRoute>} />
        <Route path="/discipulado/:id/editar" element={<AuthorizedRoute capability="DISCIPLESHIP_CLASS_CHANGE"><DiscipleshipClassEditPage /></AuthorizedRoute>} />
        <Route path="/discipulado/:classId/aulas/:lessonId/chamada" element={<DiscipleshipAttendancePage />} />
        <Route path="/discipulado/:id" element={<AuthorizedRoute capability="DISCIPLESHIP_CLASS_VIEW"><DiscipleshipClassDetailPage /></AuthorizedRoute>} />
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
