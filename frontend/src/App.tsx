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
import DiaconiaPage from './pages/DiaconiaPage'
import DiaconiaCountingCreatePage from './pages/DiaconiaCountingCreatePage'
import DiaconiaCountingDetailPage from './pages/DiaconiaCountingDetailPage'
import DiaconiaCountingEditPage from './pages/DiaconiaCountingEditPage'
import DiaconiaCountingEnvironmentsPage from './pages/DiaconiaCountingEnvironmentsPage'
import DiaconiaCountingPage from './pages/DiaconiaCountingPage'
import DiaconiaInventoryCountCreatePage from './pages/DiaconiaInventoryCountCreatePage'
import DiaconiaInventoryCountDetailPage from './pages/DiaconiaInventoryCountDetailPage'
import DiaconiaInventoryCountsPage from './pages/DiaconiaInventoryCountsPage'
import DiaconiaInventoryItemCreatePage from './pages/DiaconiaInventoryItemCreatePage'
import DiaconiaInventoryItemEditPage from './pages/DiaconiaInventoryItemEditPage'
import DiaconiaInventoryItemsPage from './pages/DiaconiaInventoryItemsPage'
import DiaconiaInventoryPage from './pages/DiaconiaInventoryPage'
import DiaconiaInventoryRegistryPage from './pages/DiaconiaInventoryRegistryPage'
import DiaconiaStockCategoriesPage from './pages/DiaconiaStockCategoriesPage'
import DiaconiaStockItemCreatePage from './pages/DiaconiaStockItemCreatePage'
import DiaconiaStockItemEditPage from './pages/DiaconiaStockItemEditPage'
import DiaconiaStockMovementCreatePage from './pages/DiaconiaStockMovementCreatePage'
import DiaconiaStockMovementsPage from './pages/DiaconiaStockMovementsPage'
import DiaconiaStockPage from './pages/DiaconiaStockPage'
import DiscipleshipClassCreatePage from './pages/DiscipleshipClassCreatePage'
import DiscipleshipClassDetailPage from './pages/DiscipleshipClassDetailPage'
import DiscipleshipClassEditPage from './pages/DiscipleshipClassEditPage'
import DiscipleshipClassesPage from './pages/DiscipleshipClassesPage'
import DiscipleshipAttendancePage from './pages/DiscipleshipAttendancePage'
import HomePage from './pages/HomePage'
import ForgotPasswordPage from './pages/ForgotPasswordPage'
import LoginPage from './pages/LoginPage'
import MembershipPage from './pages/MembershipPage'
import MyProfilePage from './pages/MyProfilePage'
import MySchedulesPage from './pages/MySchedulesPage'
import MyUnavailabilityPage from './pages/MyUnavailabilityPage'
import NotificationsPage from './pages/NotificationsPage'
import PersonCreatePage from './pages/PersonCreatePage'
import PersonEditPage from './pages/PersonEditPage'
import PersonProfilePage from './pages/PersonProfilePage'
import PeoplePage from './pages/PeoplePage'
import ScheduleDetailPage from './pages/ScheduleDetailPage'
import SchedulesPage from './pages/SchedulesPage'
import SecretaryDashboardPage from './pages/SecretaryDashboardPage'
import ResetPasswordPage from './pages/ResetPasswordPage'
import UserAccessPage from './pages/UserAccessPage'
import UsersPage from './pages/UsersPage'
import WorshipSchedulePage from './pages/WorshipSchedulePage'
import WorshipTemplatesPage from './pages/WorshipTemplatesPage'
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
        <Route path="/" element={<HomePage />} />
        <Route path="/secretaria" element={<AuthorizedRoute capability="ACCESS_REQUEST_VIEW"><SecretaryDashboardPage /></AuthorizedRoute>} />
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
        <Route path="/meu-perfil" element={<MyProfilePage />} />
        <Route path="/notificacoes" element={<NotificationsPage />} />
        <Route path="/minhas-escalas" element={<MySchedulesPage />} />
        <Route path="/minhas-indisponibilidades" element={<MyUnavailabilityPage />} />
        <Route path="/agenda-cultos" element={<AuthorizedRoute capability="WORSHIP_SCHEDULE_VIEW"><WorshipSchedulePage /></AuthorizedRoute>} />
        <Route path="/agenda-cultos/padroes" element={<AuthorizedRoute capability="WORSHIP_SCHEDULE_VIEW"><WorshipTemplatesPage /></AuthorizedRoute>} />
        <Route path="/escalas" element={<SchedulesPage />} />
        <Route path="/escalas/:id" element={<ScheduleDetailPage />} />
        <Route path="/departamentos" element={<AuthorizedRoute capability="DEPARTMENT_VIEW"><DepartmentsPage /></AuthorizedRoute>} />
        <Route path="/departamentos/novo" element={<AuthorizedRoute capability="DEPARTMENT_CREATE"><DepartmentCreatePage /></AuthorizedRoute>} />
        <Route path="/departamentos/:id/editar" element={<DepartmentEditPage />} />
        <Route path="/departamentos/:id" element={<DepartmentDetailPage />} />
        <Route path="/diaconia" element={<AuthorizedRoute capability="DIACONIA_VIEW"><DiaconiaPage /></AuthorizedRoute>} />
        <Route path="/diaconia/contagens" element={<AuthorizedRoute capability="DIACONIA_VIEW"><DiaconiaCountingPage /></AuthorizedRoute>} />
        <Route path="/diaconia/contagens/nova" element={<AuthorizedRoute capability="DIACONIA_COUNTING_MANAGE"><DiaconiaCountingCreatePage /></AuthorizedRoute>} />
        <Route path="/diaconia/contagens/:id/editar" element={<AuthorizedRoute capability="DIACONIA_COUNTING_MANAGE"><DiaconiaCountingEditPage /></AuthorizedRoute>} />
        <Route path="/diaconia/contagens/:id" element={<AuthorizedRoute capability="DIACONIA_VIEW"><DiaconiaCountingDetailPage /></AuthorizedRoute>} />
        <Route path="/diaconia/contagens/ambientes" element={<AuthorizedRoute capability="DIACONIA_VIEW"><DiaconiaCountingEnvironmentsPage /></AuthorizedRoute>} />
        <Route path="/diaconia/inventario" element={<AuthorizedRoute capability="DIACONIA_VIEW"><DiaconiaInventoryPage /></AuthorizedRoute>} />
        <Route path="/diaconia/inventario/contagens" element={<AuthorizedRoute capability="DIACONIA_VIEW"><DiaconiaInventoryCountsPage /></AuthorizedRoute>} />
        <Route path="/diaconia/inventario/contagens/nova" element={<AuthorizedRoute capability="DIACONIA_INVENTORY_MANAGE"><DiaconiaInventoryCountCreatePage /></AuthorizedRoute>} />
        <Route path="/diaconia/inventario/contagens/:id" element={<AuthorizedRoute capability="DIACONIA_VIEW"><DiaconiaInventoryCountDetailPage /></AuthorizedRoute>} />
        <Route path="/diaconia/inventario/itens" element={<AuthorizedRoute capability="DIACONIA_VIEW"><DiaconiaInventoryItemsPage /></AuthorizedRoute>} />
        <Route path="/diaconia/inventario/itens/novo" element={<AuthorizedRoute capability="DIACONIA_INVENTORY_MANAGE"><DiaconiaInventoryItemCreatePage /></AuthorizedRoute>} />
        <Route path="/diaconia/inventario/itens/:id/editar" element={<AuthorizedRoute capability="DIACONIA_INVENTORY_MANAGE"><DiaconiaInventoryItemEditPage /></AuthorizedRoute>} />
        <Route path="/diaconia/inventario/categorias" element={<AuthorizedRoute capability="DIACONIA_VIEW"><DiaconiaInventoryRegistryPage kind="categories" /></AuthorizedRoute>} />
        <Route path="/diaconia/inventario/locais" element={<AuthorizedRoute capability="DIACONIA_VIEW"><DiaconiaInventoryRegistryPage kind="locations" /></AuthorizedRoute>} />
        <Route path="/diaconia/estoque" element={<AuthorizedRoute capability="DIACONIA_VIEW"><DiaconiaStockPage /></AuthorizedRoute>} />
        <Route path="/diaconia/estoque/novo" element={<AuthorizedRoute capability="DIACONIA_STOCK_MANAGE"><DiaconiaStockItemCreatePage /></AuthorizedRoute>} />
        <Route path="/diaconia/estoque/entrada" element={<AuthorizedRoute capability="DIACONIA_STOCK_MANAGE"><DiaconiaStockMovementCreatePage movementType="ENTRADA" /></AuthorizedRoute>} />
        <Route path="/diaconia/estoque/saida" element={<AuthorizedRoute capability="DIACONIA_STOCK_MANAGE"><DiaconiaStockMovementCreatePage movementType="SAIDA" /></AuthorizedRoute>} />
        <Route path="/diaconia/estoque/movimentacoes" element={<AuthorizedRoute capability="DIACONIA_VIEW"><DiaconiaStockMovementsPage /></AuthorizedRoute>} />
        <Route path="/diaconia/estoque/categorias" element={<AuthorizedRoute capability="DIACONIA_VIEW"><DiaconiaStockCategoriesPage /></AuthorizedRoute>} />
        <Route path="/diaconia/estoque/:id/editar" element={<AuthorizedRoute capability="DIACONIA_STOCK_MANAGE"><DiaconiaStockItemEditPage /></AuthorizedRoute>} />
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
        <Route path="/esqueci-minha-senha" element={<ForgotPasswordPage />} />
        <Route path="/redefinir-senha/:uid/:token" element={<ResetPasswordPage />} />
        <Route path="/*" element={<AdminRoutes />} />
      </Routes>
    </BrowserRouter>
  )
}

export default App
