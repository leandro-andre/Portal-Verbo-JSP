import { BookOpenCheck, Building2, CalendarX2, ClipboardList, ShieldCheck, UserCog, UsersRound } from 'lucide-react'
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
  const hasAccessItems = canViewAccessRequests || canViewUsers

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
        {!isCollapsed ? <p className="sidebar__section-label">Minha area</p> : null}
        <NavLink
          className={({ isActive }) => `sidebar__link${isActive ? ' sidebar__link--active' : ''}`}
          to="/minhas-indisponibilidades"
        >
          <CalendarX2 size={18} aria-hidden="true" />
          {!isCollapsed ? <span>Minhas indisponibilidades</span> : null}
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

        {canViewDepartments && !isCollapsed ? (
          <p className="sidebar__section-label sidebar__section-label--spaced">Igreja</p>
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
      </nav>

      <div className="sidebar__user">
        <div className="sidebar__user-avatar" aria-hidden="true">
          UP
        </div>
        {!isCollapsed ? (
          <div className="sidebar__user-copy">
            <strong>Usuario do portal</strong>
            <span>Acesso administrativo</span>
          </div>
        ) : null}
      </div>
    </aside>
  )
}

export default Sidebar
