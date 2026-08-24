import { useState, type ReactNode } from 'react'
import { useLocation } from 'react-router-dom'
import Sidebar from './Sidebar'
import Topbar from './Topbar'

type AppShellProps = {
  children: ReactNode
}

function AppShell({ children }: AppShellProps) {
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(false)
  const location = useLocation()
  const topbarTitle = location.pathname.startsWith('/usuarios') || location.pathname.endsWith('/acesso')
    ? 'Usuarios'
    : location.pathname.startsWith('/solicitacoes-acesso')
      ? 'Solicitacoes'
      : location.pathname.startsWith('/agenda-cultos')
        ? 'Agenda de Cultos'
        : location.pathname.startsWith('/escalas')
          ? 'Escalas'
        : location.pathname.startsWith('/departamentos')
          ? 'Departamentos'
          : location.pathname.startsWith('/discipulado')
            ? 'Discipulado'
            : location.pathname.startsWith('/membresia')
              ? 'Membresia'
              : 'Pessoas'

  return (
    <div className={`app-shell${isSidebarCollapsed ? ' app-shell--collapsed' : ''}`}>
      <Sidebar isCollapsed={isSidebarCollapsed} />
      <div className="app-shell__body">
        <Topbar
          title={topbarTitle}
          isSidebarCollapsed={isSidebarCollapsed}
          onToggleSidebar={() => setIsSidebarCollapsed((current) => !current)}
        />
        <main className="app-main">{children}</main>
      </div>
    </div>
  )
}

export default AppShell
