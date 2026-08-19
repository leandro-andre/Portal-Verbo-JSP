import { Bell, LogOut, PanelLeftClose, PanelLeftOpen } from 'lucide-react'
import { useLogout, useCurrentUser } from '../../hooks/useAuth'

type TopbarProps = {
  title: string
  isSidebarCollapsed: boolean
  onToggleSidebar: () => void
}

function Topbar({ title, isSidebarCollapsed, onToggleSidebar }: TopbarProps) {
  const ToggleIcon = isSidebarCollapsed ? PanelLeftOpen : PanelLeftClose
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
          className="icon-button"
          type="button"
          onClick={onToggleSidebar}
          aria-label={isSidebarCollapsed ? 'Expandir menu lateral' : 'Recolher menu lateral'}
        >
          <ToggleIcon size={19} aria-hidden="true" />
        </button>
        <span className="topbar__title">{title}</span>
      </div>

      <div className="topbar__actions">
        <button className="icon-button" type="button" aria-label="Notificacoes">
          <Bell size={18} aria-hidden="true" />
        </button>
        <div className="topbar__user" aria-label="Usuario atual">
          <span className="topbar__user-avatar" aria-hidden="true">
            {initials}
          </span>
          <span className="topbar__user-copy">
            <span className="topbar__user-name">{displayName}</span>
            <span className="topbar__user-role">{roleLabel}</span>
          </span>
        </div>
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
