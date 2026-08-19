import './App.css'
import PortalHeader from './components/PortalHeader'
import PeoplePage from './pages/PeoplePage'

function App() {
  return (
    <div className="app-shell">
      <PortalHeader />
      <main className="app-main">
        <PeoplePage />
      </main>
    </div>
  )
}

export default App
