import { useEffect, useState, type ReactNode } from 'react'
import { useLocation } from 'react-router-dom'
import Sidebar from './Sidebar'
import Topbar from './Topbar'

type AppShellProps = {
  children: ReactNode
}

function AppShell({ children }: AppShellProps) {
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(false)
  const [isMobileSidebarOpen, setIsMobileSidebarOpen] = useState(false)
  const location = useLocation()
  const topbarTitle = location.pathname === '/'
    ? 'Inicio'
    : location.pathname.startsWith('/meu-perfil') || location.pathname.startsWith('/minhas-')
      ? 'Minha Area'
    : location.pathname.startsWith('/usuarios') || location.pathname.endsWith('/acesso')
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

  useEffect(() => {
    if (!isMobileSidebarOpen) {
      return
    }

    const previousOverflow = document.body.style.overflow
    document.body.style.overflow = 'hidden'
    const focusTimer = window.setTimeout(() => {
      document.querySelector<HTMLElement>('#app-sidebar a')?.focus()
    }, 0)

    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        setIsMobileSidebarOpen(false)
      }
    }

    window.addEventListener('keydown', handleKeyDown)
    return () => {
      window.clearTimeout(focusTimer)
      document.body.style.overflow = previousOverflow
      window.removeEventListener('keydown', handleKeyDown)
    }
  }, [isMobileSidebarOpen])

  return (
    <div className={`app-shell${isSidebarCollapsed ? ' app-shell--collapsed' : ''}${isMobileSidebarOpen ? ' app-shell--mobile-open' : ''}`}>
      <Sidebar
        id="app-sidebar"
        isCollapsed={isSidebarCollapsed}
        isMobileOpen={isMobileSidebarOpen}
        onNavigate={() => setIsMobileSidebarOpen(false)}
      />
      <button
        className="app-shell__backdrop"
        type="button"
        aria-label="Fechar menu lateral"
        aria-hidden={!isMobileSidebarOpen}
        tabIndex={isMobileSidebarOpen ? 0 : -1}
        onClick={() => setIsMobileSidebarOpen(false)}
      />
      <div className="app-shell__body">
        <Topbar
          title={topbarTitle}
          isSidebarCollapsed={isSidebarCollapsed}
          isMobileSidebarOpen={isMobileSidebarOpen}
          onToggleDesktopSidebar={() => setIsSidebarCollapsed((current) => !current)}
          onToggleMobileSidebar={() => setIsMobileSidebarOpen((current) => !current)}
        />
        <main className="app-main">{children}</main>
      </div>
    </div>
  )
}

export default AppShell
