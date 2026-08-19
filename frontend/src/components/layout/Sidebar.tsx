import { UsersRound } from 'lucide-react'
import { Link } from 'react-router-dom'

type SidebarProps = {
  isCollapsed: boolean
}

function Sidebar({ isCollapsed }: SidebarProps) {
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
        {!isCollapsed ? <p className="sidebar__section-label">Pessoas</p> : null}
        <Link className="sidebar__link sidebar__link--active" to="/pessoas" aria-current="page">
          <UsersRound size={18} aria-hidden="true" />
          {!isCollapsed ? <span>Pessoas</span> : null}
        </Link>
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
