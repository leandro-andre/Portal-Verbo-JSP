import { BookOpenCheck, Building2, CalendarCheck2, CalendarClock, CalendarDays, CalendarX2, ClipboardList, House, ShieldCheck, UserCog, UserRound, UsersRound } from 'lucide-react'
import { NavLink } from 'react-router-dom'
import { useCurrentUser } from '../../hooks/useAuth'

type SidebarProps = {
  isCollapsed: boolean
}

function Sidebar({ isCollapsed }: SidebarProps) {
  const { data: currentUser } = useCurrentUser()
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
    <aside className="sidebar" aria-label="Navegacao principal">
      <div className="sidebar__brand">
        <div className="sidebar__brand-mark" aria-hidden="true">
          VV
        </div>
        {!isCollapsed ? (
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
        >
          <House size={18} aria-hidden="true" />
          {!isCollapsed ? <span>Inicio</span> : null}
        </NavLink>

        {!isCollapsed ? <p className="sidebar__section-label">Minha area</p> : null}
        {hasPerson ? (
          <>
            <NavLink
              className={({ isActive }) => `sidebar__link${isActive ? ' sidebar__link--active' : ''}`}
              to="/minhas-escalas"
            >
              <CalendarCheck2 size={18} aria-hidden="true" />
              {!isCollapsed ? <span>Minhas Escalas</span> : null}
            </NavLink>
            <NavLink
              className={({ isActive }) => `sidebar__link${isActive ? ' sidebar__link--active' : ''}`}
              to="/minhas-indisponibilidades"
            >
              <CalendarX2 size={18} aria-hidden="true" />
              {!isCollapsed ? <span>Minhas indisponibilidades</span> : null}
            </NavLink>
          </>
        ) : null}
        <NavLink
          className={({ isActive }) => `sidebar__link${isActive ? ' sidebar__link--active' : ''}`}
          to="/meu-perfil"
        >
          <UserRound size={18} aria-hidden="true" />
          {!isCollapsed ? <span>Meu Perfil</span> : null}
        </NavLink>

        {canViewPeople ? (
          <>
            {!isCollapsed ? <p className="sidebar__section-label sidebar__section-label--spaced">Pessoas</p> : null}
            <NavLink
              className={({ isActive }) => `sidebar__link${isActive ? ' sidebar__link--active' : ''}`}
              to="/pessoas"
            >
              <UsersRound size={18} aria-hidden="true" />
              {!isCollapsed ? <span>Pessoas</span> : null}
            </NavLink>
          </>
        ) : null}

        {hasAccessItems && !isCollapsed ? (
          <p className="sidebar__section-label sidebar__section-label--spaced">Acessos</p>
        ) : null}
        {canViewAccessRequests ? (
          <NavLink
            className={({ isActive }) => `sidebar__link${isActive ? ' sidebar__link--active' : ''}`}
            to="/solicitacoes-acesso"
          >
            <ClipboardList size={18} aria-hidden="true" />
            {!isCollapsed ? <span>Solicitacoes</span> : null}
          </NavLink>
        ) : null}
        {canViewUsers ? (
          <NavLink
            className={({ isActive }) => `sidebar__link${isActive ? ' sidebar__link--active' : ''}`}
            to="/usuarios"
          >
            <UserCog size={18} aria-hidden="true" />
            {!isCollapsed ? <span>Usuarios</span> : null}
          </NavLink>
        ) : null}

        {(canViewDiscipleship || canViewMembership) && !isCollapsed ? (
          <p className="sidebar__section-label sidebar__section-label--spaced">Jornada</p>
        ) : null}
        {canViewDiscipleship ? (
          <NavLink
            className={({ isActive }) => `sidebar__link${isActive ? ' sidebar__link--active' : ''}`}
            to="/discipulado"
          >
            <BookOpenCheck size={18} aria-hidden="true" />
            {!isCollapsed ? <span>Discipulado</span> : null}
          </NavLink>
        ) : null}
        {canViewMembership ? (
          <NavLink
            className={({ isActive }) => `sidebar__link${isActive ? ' sidebar__link--active' : ''}`}
            to="/membresia"
          >
            <ShieldCheck size={18} aria-hidden="true" />
            {!isCollapsed ? <span>Membresia</span> : null}
          </NavLink>
        ) : null}

        {(canViewDepartments || canViewWorshipSchedule || canViewSchedules) && !isCollapsed ? (
          <p className="sidebar__section-label sidebar__section-label--spaced">Igreja</p>
        ) : null}
        {canViewWorshipSchedule ? (
          <NavLink
            className={({ isActive }) => `sidebar__link${isActive ? ' sidebar__link--active' : ''}`}
            to="/agenda-cultos"
          >
            <CalendarClock size={18} aria-hidden="true" />
            {!isCollapsed ? <span>Agenda de Cultos</span> : null}
          </NavLink>
        ) : null}
        {canViewDepartments ? (
          <NavLink
            className={({ isActive }) => `sidebar__link${isActive ? ' sidebar__link--active' : ''}`}
            to="/departamentos"
          >
            <Building2 size={18} aria-hidden="true" />
            {!isCollapsed ? <span>Departamentos</span> : null}
          </NavLink>
        ) : null}
        {canViewSchedules ? (
          <NavLink
            className={({ isActive }) => `sidebar__link${isActive ? ' sidebar__link--active' : ''}`}
            to="/escalas"
          >
            <CalendarDays size={18} aria-hidden="true" />
            {!isCollapsed ? <span>Escalas</span> : null}
          </NavLink>
        ) : null}
      </nav>

      <div className="sidebar__user">
        <div className="sidebar__user-avatar" aria-hidden="true">
          {currentUser?.user?.photo_url ? <img src={currentUser.user.photo_url} alt="" /> : initials}
        </div>
        {!isCollapsed ? (
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
