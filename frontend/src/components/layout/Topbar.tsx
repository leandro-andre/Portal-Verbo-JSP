import { Bell, PanelLeftClose, PanelLeftOpen } from 'lucide-react'

type TopbarProps = {
  title: string
  isSidebarCollapsed: boolean
  onToggleSidebar: () => void
}

function Topbar({ title, isSidebarCollapsed, onToggleSidebar }: TopbarProps) {
  const ToggleIcon = isSidebarCollapsed ? PanelLeftOpen : PanelLeftClose

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
            UP
          </span>
          <span className="topbar__user-name">Usuario</span>
        </div>
      </div>
    </header>
  )
}

export default Topbar
