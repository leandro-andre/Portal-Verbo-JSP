import { useState, type ReactNode } from 'react'
import Sidebar from './Sidebar'
import Topbar from './Topbar'

type AppShellProps = {
  children: ReactNode
}

function AppShell({ children }: AppShellProps) {
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(false)

  return (
    <div className={`app-shell${isSidebarCollapsed ? ' app-shell--collapsed' : ''}`}>
      <Sidebar isCollapsed={isSidebarCollapsed} />
      <div className="app-shell__body">
        <Topbar
          title="Pessoas"
          isSidebarCollapsed={isSidebarCollapsed}
          onToggleSidebar={() => setIsSidebarCollapsed((current) => !current)}
        />
        <main className="app-main">{children}</main>
      </div>
    </div>
  )
}

export default AppShell
