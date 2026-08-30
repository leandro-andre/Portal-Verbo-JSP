import { useEffect, useState } from 'react'
import { Plus, Search } from 'lucide-react'
import { Link, useLocation, useNavigate } from 'react-router-dom'
import PeopleTable from '../components/people/PeopleTable'
import { useCan } from '../hooks/useAuth'
import { usePeople } from '../hooks/usePeople'

type StatusFilter = 'ALL' | 'ACTIVE' | 'INACTIVE'

function PeoplePage() {
  const location = useLocation()
  const navigate = useNavigate()
  const [search, setSearch] = useState('')
  const [statusFilter, setStatusFilter] = useState<StatusFilter>('ALL')
  const [successMessage] = useState(() => {
    const state = location.state as { successMessage?: string } | null
    return state?.successMessage ?? null
  })
  const { data: people = [], isError, isLoading, refetch } = usePeople()
  const canCreatePeople = useCan('PEOPLE_CREATE')
  const normalizedSearch = search.trim().toLowerCase()

  const filteredPeople = people.filter((person) => {
    const matchesStatus = statusFilter === 'ALL' || person.status === statusFilter
    const matchesSearch =
      !normalizedSearch ||
      person.display_name.toLowerCase().includes(normalizedSearch) ||
      person.full_name.toLowerCase().includes(normalizedSearch) ||
      person.email.toLowerCase().includes(normalizedSearch) ||
      person.phone.toLowerCase().includes(normalizedSearch)

    return matchesStatus && matchesSearch
  })

  const hasPeople = people.length > 0
  const countLabel = `${filteredPeople.length} ${filteredPeople.length === 1 ? 'pessoa' : 'pessoas'}`

  useEffect(() => {
    if (location.state) {
      navigate(location.pathname, { replace: true, state: null })
    }
  }, [location.pathname, location.state, navigate])

  return (
    <section className="people-page" id="pessoas">
      <div className="page-heading">
        <div>
          <h1>Pessoas</h1>
          <p className="page-heading__description">
            Gerencie as pessoas cadastradas na igreja.
          </p>
        </div>

        {canCreatePeople ? (
          <Link
            className="button button--primary"
            to="/pessoas/nova"
          >
            <Plus size={17} aria-hidden="true" />
            Nova pessoa
          </Link>
        ) : null}
      </div>

      {successMessage ? (
        <div className="form-alert form-alert--success" role="status">
          {successMessage}
        </div>
      ) : null}

      <div className="people-toolbar" aria-label="Filtros de pessoas">
        <label className="search-field" htmlFor="people-search">
          <span className="search-field__icon" aria-hidden="true">
            <Search size={18} />
          </span>
          <span className="sr-only">Buscar por nome, e-mail ou celular/WhatsApp</span>
          <input
            id="people-search"
            type="search"
            placeholder="Buscar por nome, e-mail ou celular/WhatsApp..."
            value={search}
            onChange={(event) => setSearch(event.target.value)}
          />
        </label>

        <label className="status-filter" htmlFor="people-status-filter">
          <span>Status</span>
          <select
            id="people-status-filter"
            value={statusFilter}
            onChange={(event) => setStatusFilter(event.target.value as StatusFilter)}
          >
            <option value="ALL">Todos</option>
            <option value="ACTIVE">Ativos</option>
            <option value="INACTIVE">Inativos</option>
          </select>
        </label>
      </div>

      <div className="people-summary" aria-live="polite">
        {countLabel}
      </div>

      {isLoading ? (
        <div className="state-panel">
          <h2>Carregando pessoas...</h2>
          <p>Aguarde enquanto os dados sao carregados.</p>
        </div>
      ) : isError ? (
        <div className="state-panel state-panel--error">
          <h2>Nao foi possivel carregar as pessoas.</h2>
          <p>Verifique a conexao com o backend e tente novamente.</p>
          <button className="button button--secondary" type="button" onClick={() => void refetch()}>
            Tentar novamente
          </button>
        </div>
      ) : filteredPeople.length > 0 ? (
        <PeopleTable people={filteredPeople} />
      ) : (
        <div className="state-panel">
          {hasPeople ? (
            <>
              <h2>Nenhuma pessoa encontrada para os filtros atuais.</h2>
              <p>Ajuste a busca ou o filtro de status.</p>
            </>
          ) : (
            <>
              <h2>Nenhuma pessoa cadastrada.</h2>
              <p>Quando houver pessoas cadastradas, elas aparecerao aqui.</p>
            </>
          )}
        </div>
      )}
    </section>
  )
}

export default PeoplePage
