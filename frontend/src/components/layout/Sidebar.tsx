import { BookOpenCheck, Building2, CalendarCheck2, CalendarClock, CalendarDays, CalendarX2, ClipboardList, House, ShieldCheck, UserCog, UserRound, UsersRound } from 'lucide-react'
import { NavLink } from 'react-router-dom'
import { useCurrentUser } from '../../hooks/useAuth'

type SidebarProps = {
  id?: string
  isCollapsed: boolean
  isMobileOpen: boolean
  onNavigate: () => void
}

function Sidebar({ id, isCollapsed, isMobileOpen, onNavigate }: SidebarProps) {
  const { data: currentUser } = useCurrentUser()
  const showExpandedContent = !isCollapsed || isMobileOpen
  const capabilities = currentUser?.user?.capabilities ?? []
  const canViewPeople = capabilities.includes('PEOPLE_VIEW')
  const canViewAccessRequests = capabilities.includes('ACCESS_REQUEST_VIEW')
  const canViewUsers = capabilities.includes('USER_VIEW')
  const canViewDiscipleship = capabilities.includes('DISCIPLESHIP_CLASS_VIEW')
  const canViewMembership = capabilities.includes('MEMBERSHIP_VIEW')
  const canViewDepartments = capabilities.includes('DEPARTMENT_VIEW')
  const canViewWorshipSchedule = capabilities.includes('WORSHIP_SCHEDULE_VIEW')
  const canViewSchedules = capabilities.includes('SCHEDULE_VIEW')
  const hasPerson = Boolean(currentUser?.user?.person_id)
  const hasAccessItems = canViewAccessRequests || canViewUsers
  const displayName = currentUser?.user?.display_name || 'Usuario do portal'
  const roleLabel = currentUser?.user?.roles[0]
    ? {
        PORTAL_ADMIN: 'Administrador do Portal',
        SECRETARY: 'Secretaria',
        PASTOR: 'Pastor',
      }[currentUser.user.roles[0]]
    : 'Acesso ao portal'
  const initials = displayName
    .split(' ')
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part[0])
    .join('')
    .toUpperCase() || 'UP'

  return (
    <aside
      id={id}
      className="sidebar"
      aria-label="Navegacao principal"
    >
      <div className="sidebar__brand">
        <div className="sidebar__brand-mark" aria-hidden="true">
          VV
        </div>
        {showExpandedContent ? (
          <div className="sidebar__brand-copy">
            <strong>Verbo da Vida</strong>
            <span>Jardim Sao Paulo</span>
          </div>
        ) : null}
      </div>

      <nav className="sidebar__nav" aria-label="Modulos do portal">
        <NavLink
          className={({ isActive }) => `sidebar__link${isActive ? ' sidebar__link--active' : ''}`}
          to="/"
          end
          onClick={onNavigate}
        >
          <House size={18} aria-hidden="true" />
          {showExpandedContent ? <span>Inicio</span> : null}
        </NavLink>

        {showExpandedContent ? <p className="sidebar__section-label">Minha area</p> : null}
        {hasPerson ? (
          <>
            <NavLink
              className={({ isActive }) => `sidebar__link${isActive ? ' sidebar__link--active' : ''}`}
              to="/minhas-escalas"
              onClick={onNavigate}
            >
              <CalendarCheck2 size={18} aria-hidden="true" />
              {showExpandedContent ? <span>Minhas Escalas</span> : null}
            </NavLink>
            <NavLink
              className={({ isActive }) => `sidebar__link${isActive ? ' sidebar__link--active' : ''}`}
              to="/minhas-indisponibilidades"
              onClick={onNavigate}
            >
              <CalendarX2 size={18} aria-hidden="true" />
              {showExpandedContent ? <span>Minhas indisponibilidades</span> : null}
            </NavLink>
          </>
        ) : null}
        <NavLink
          className={({ isActive }) => `sidebar__link${isActive ? ' sidebar__link--active' : ''}`}
          to="/meu-perfil"
          onClick={onNavigate}
        >
          <UserRound size={18} aria-hidden="true" />
          {showExpandedContent ? <span>Meu Perfil</span> : null}
        </NavLink>

        {canViewPeople ? (
          <>
            {showExpandedContent ? <p className="sidebar__section-label sidebar__section-label--spaced">Pessoas</p> : null}
            <NavLink
              className={({ isActive }) => `sidebar__link${isActive ? ' sidebar__link--active' : ''}`}
              to="/pessoas"
              onClick={onNavigate}
            >
              <UsersRound size={18} aria-hidden="true" />
              {showExpandedContent ? <span>Pessoas</span> : null}
            </NavLink>
          </>
        ) : null}

        {hasAccessItems && showExpandedContent ? (
          <p className="sidebar__section-label sidebar__section-label--spaced">Acessos</p>
        ) : null}
        {canViewAccessRequests ? (
          <NavLink
            className={({ isActive }) => `sidebar__link${isActive ? ' sidebar__link--active' : ''}`}
            to="/solicitacoes-acesso"
            onClick={onNavigate}
          >
            <ClipboardList size={18} aria-hidden="true" />
            {showExpandedContent ? <span>Solicitacoes</span> : null}
          </NavLink>
        ) : null}
        {canViewUsers ? (
          <NavLink
            className={({ isActive }) => `sidebar__link${isActive ? ' sidebar__link--active' : ''}`}
            to="/usuarios"
            onClick={onNavigate}
          >
            <UserCog size={18} aria-hidden="true" />
            {showExpandedContent ? <span>Usuarios</span> : null}
          </NavLink>
        ) : null}

        {(canViewDiscipleship || canViewMembership) && showExpandedContent ? (
          <p className="sidebar__section-label sidebar__section-label--spaced">Jornada</p>
        ) : null}
        {canViewDiscipleship ? (
          <NavLink
            className={({ isActive }) => `sidebar__link${isActive ? ' sidebar__link--active' : ''}`}
            to="/discipulado"
            onClick={onNavigate}
          >
            <BookOpenCheck size={18} aria-hidden="true" />
            {showExpandedContent ? <span>Discipulado</span> : null}
          </NavLink>
        ) : null}
        {canViewMembership ? (
          <NavLink
            className={({ isActive }) => `sidebar__link${isActive ? ' sidebar__link--active' : ''}`}
            to="/membresia"
            onClick={onNavigate}
          >
            <ShieldCheck size={18} aria-hidden="true" />
            {showExpandedContent ? <span>Membresia</span> : null}
          </NavLink>
        ) : null}

        {(canViewDepartments || canViewWorshipSchedule || canViewSchedules) && showExpandedContent ? (
          <p className="sidebar__section-label sidebar__section-label--spaced">Igreja</p>
        ) : null}
        {canViewWorshipSchedule ? (
          <NavLink
            className={({ isActive }) => `sidebar__link${isActive ? ' sidebar__link--active' : ''}`}
            to="/agenda-cultos"
            onClick={onNavigate}
          >
            <CalendarClock size={18} aria-hidden="true" />
            {showExpandedContent ? <span>Agenda de Cultos</span> : null}
          </NavLink>
        ) : null}
        {canViewDepartments ? (
          <NavLink
            className={({ isActive }) => `sidebar__link${isActive ? ' sidebar__link--active' : ''}`}
            to="/departamentos"
            onClick={onNavigate}
          >
            <Building2 size={18} aria-hidden="true" />
            {showExpandedContent ? <span>Departamentos</span> : null}
          </NavLink>
        ) : null}
        {canViewSchedules ? (
          <NavLink
            className={({ isActive }) => `sidebar__link${isActive ? ' sidebar__link--active' : ''}`}
            to="/escalas"
            onClick={onNavigate}
          >
            <CalendarDays size={18} aria-hidden="true" />
            {showExpandedContent ? <span>Escalas</span> : null}
          </NavLink>
        ) : null}
      </nav>

      <div className="sidebar__user">
        <div className="sidebar__user-avatar" aria-hidden="true">
          {currentUser?.user?.photo_url ? <img src={currentUser.user.photo_url} alt="" /> : initials}
        </div>
        {showExpandedContent ? (
          <div className="sidebar__user-copy">
            <strong>{displayName}</strong>
            <span>{roleLabel}</span>
          </div>
        ) : null}
      </div>
    </aside>
  )
}

export default Sidebar
