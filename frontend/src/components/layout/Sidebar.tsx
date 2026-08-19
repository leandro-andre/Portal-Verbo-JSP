import { ClipboardList, UserCog, UsersRound } from 'lucide-react'
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
        {canViewPeople ? (
          <>
            {!isCollapsed ? <p className="sidebar__section-label">Pessoas</p> : null}
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
