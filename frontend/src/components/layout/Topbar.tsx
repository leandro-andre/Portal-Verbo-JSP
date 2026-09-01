import { Bell, LogOut, Menu, PanelLeftClose, PanelLeftOpen, X } from 'lucide-react'
import { Link } from 'react-router-dom'
import { useLogout, useCurrentUser } from '../../hooks/useAuth'

type TopbarProps = {
  title: string
  isSidebarCollapsed: boolean
  isMobileSidebarOpen: boolean
  onToggleDesktopSidebar: () => void
  onToggleMobileSidebar: () => void
}

function Topbar({
  title,
  isSidebarCollapsed,
  isMobileSidebarOpen,
  onToggleDesktopSidebar,
  onToggleMobileSidebar,
}: TopbarProps) {
  const ToggleIcon = isSidebarCollapsed ? PanelLeftOpen : PanelLeftClose
  const MobileToggleIcon = isMobileSidebarOpen ? X : Menu
  const { data: currentUser } = useCurrentUser()
  const logout = useLogout()
  const displayName = currentUser?.user?.display_name || 'Usuario'
  const roleLabel = currentUser?.user?.roles[0]
    ? {
        PORTAL_ADMIN: 'Administrador do Portal',
        SECRETARY: 'Secretaria',
        PASTOR: 'Pastor',
      }[currentUser.user.roles[0]]
    : 'Acesso administrativo'
  const initials = displayName
    .split(' ')
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part[0])
    .join('')
    .toUpperCase() || 'UP'

  return (
    <header className="topbar">
      <div className="topbar__left">
        <button
          className="icon-button topbar__sidebar-toggle topbar__sidebar-toggle--desktop"
          type="button"
          onClick={onToggleDesktopSidebar}
          aria-label={isSidebarCollapsed ? 'Expandir menu lateral' : 'Recolher menu lateral'}
          aria-expanded={!isSidebarCollapsed}
          aria-controls="app-sidebar"
        >
          <ToggleIcon size={19} aria-hidden="true" />
        </button>
        <button
          className="icon-button topbar__sidebar-toggle topbar__sidebar-toggle--mobile"
          type="button"
          onClick={onToggleMobileSidebar}
          aria-label={isMobileSidebarOpen ? 'Fechar menu lateral' : 'Abrir menu lateral'}
          aria-expanded={isMobileSidebarOpen}
          aria-controls="app-sidebar"
        >
          <MobileToggleIcon size={19} aria-hidden="true" />
        </button>
        <span className="topbar__title">{title}</span>
      </div>

      <div className="topbar__actions">
        <button className="icon-button" type="button" aria-label="Notificacoes">
          <Bell size={18} aria-hidden="true" />
        </button>
        <Link className="topbar__user topbar__user-link" aria-label="Meu Perfil" to="/meu-perfil">
          <span className="topbar__user-avatar" aria-hidden="true">
            {currentUser?.user?.photo_url ? <img src={currentUser.user.photo_url} alt="" /> : initials}
          </span>
          <span className="topbar__user-copy">
            <span className="topbar__user-name">{displayName}</span>
            <span className="topbar__user-role">{roleLabel}</span>
          </span>
        </Link>
        <button
          className="icon-button"
          type="button"
          aria-label="Sair"
          disabled={logout.isPending}
          onClick={() => void logout.mutateAsync()}
        >
          <LogOut size={18} aria-hidden="true" />
        </button>
      </div>
    </header>
  )
}

export default Topbar
