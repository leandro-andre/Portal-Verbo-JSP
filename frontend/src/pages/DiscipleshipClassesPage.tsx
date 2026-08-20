import { useMemo, useState } from 'react'
import { ChevronRight, Plus, Search } from 'lucide-react'
import { Link } from 'react-router-dom'
import DiscipleshipStatusBadge from '../components/discipleship/DiscipleshipStatusBadge'
import { useCan } from '../hooks/useAuth'
import { useDiscipleshipClasses } from '../hooks/useDiscipleshipClasses'
import type { DiscipleshipClass, DiscipleshipClassStatus } from '../types/discipleship'
import { formatDate } from '../utils/discipleship'

type ClassFilter = 'ALL' | DiscipleshipClassStatus

const FILTERS: Array<{ label: string; value: ClassFilter }> = [
  { label: 'Todas', value: 'ALL' },
  { label: 'Planejadas', value: 'PLANNED' },
  { label: 'Em andamento', value: 'IN_PROGRESS' },
  { label: 'Concluidas', value: 'COMPLETED' },
  { label: 'Canceladas', value: 'CANCELLED' },
]

function DiscipleshipClassesTable({ classes }: { classes: DiscipleshipClass[] }) {
  return (
    <div className="table-shell">
      <table className="people-table">
        <thead>
          <tr>
            <th scope="col">Turma</th>
            <th scope="col">Professor</th>
            <th scope="col">Periodo</th>
            <th scope="col">Aulas</th>
            <th scope="col">Status</th>
            <th scope="col" className="people-table__actions-header">Acao</th>
          </tr>
        </thead>
        <tbody>
          {classes.map((discipleshipClass) => (
            <tr key={discipleshipClass.id}>
              <td>
                <Link className="person-name-link" to={`/discipulado/${discipleshipClass.id}`}>
                  {discipleshipClass.name}
                </Link>
              </td>
              <td>{discipleshipClass.teacher.display_name}</td>
              <td>{formatDate(discipleshipClass.start_date)} - {formatDate(discipleshipClass.expected_end_date)}</td>
              <td>{discipleshipClass.planned_sessions}</td>
              <td><DiscipleshipStatusBadge status={discipleshipClass.status} /></td>
              <td>
                <Link
                  className="icon-button icon-button--table"
                  to={`/discipulado/${discipleshipClass.id}`}
                  aria-label={`Abrir turma ${discipleshipClass.name}`}
                >
                  <ChevronRight size={18} aria-hidden="true" />
                </Link>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

function groupClasses(classes: DiscipleshipClass[]) {
  return {
    current: classes.find((item) => item.status === 'IN_PROGRESS') ?? null,
    planned: classes.filter((item) => item.status === 'PLANNED'),
    history: classes.filter((item) => item.status === 'COMPLETED' || item.status === 'CANCELLED'),
  }
}

function DiscipleshipClassesPage() {
  const [search, setSearch] = useState('')
  const [filter, setFilter] = useState<ClassFilter>('ALL')
  const canCreate = useCan('DISCIPLESHIP_CLASS_CREATE')
  const { data: classes = [], isError, isLoading, refetch } = useDiscipleshipClasses()
  const normalizedSearch = search.trim().toLowerCase()

  const filteredClasses = useMemo(
    () =>
      classes.filter((item) => {
        const matchesFilter = filter === 'ALL' || item.status === filter
        const matchesSearch =
          !normalizedSearch ||
          item.name.toLowerCase().includes(normalizedSearch) ||
          item.teacher.display_name.toLowerCase().includes(normalizedSearch)

        return matchesFilter && matchesSearch
      }),
    [classes, filter, normalizedSearch],
  )
  const grouped = groupClasses(classes)

  return (
    <section className="people-page">
      <div className="page-heading">
        <div>
          <h1>Discipulado</h1>
          <p className="page-heading__description">Gerencie as turmas de discipulado.</p>
        </div>

        {canCreate ? (
          <Link className="button button--primary" to="/discipulado/nova">
            <Plus size={17} aria-hidden="true" />
            Nova turma
          </Link>
        ) : null}
      </div>

      {grouped.current ? (
        <section className="state-panel state-panel--compact">
          <h2>{grouped.current.name}</h2>
          <p>{grouped.current.teacher.display_name} | {formatDate(grouped.current.start_date)} - {formatDate(grouped.current.expected_end_date)}</p>
          <Link className="button button--secondary" to={`/discipulado/${grouped.current.id}`}>
            Ver turma em andamento
          </Link>
        </section>
      ) : null}

      <div className="people-toolbar" aria-label="Filtros de turmas de discipulado">
        <label className="search-field" htmlFor="discipleship-search">
          <span className="search-field__icon" aria-hidden="true"><Search size={18} /></span>
          <span className="sr-only">Buscar por turma ou professor</span>
          <input
            id="discipleship-search"
            type="search"
            placeholder="Buscar por turma ou professor..."
            value={search}
            onChange={(event) => setSearch(event.target.value)}
          />
        </label>

        <div className="segmented-filter" aria-label="Status da turma">
          {FILTERS.map((item) => (
            <button
              key={item.value}
              className={`segmented-filter__button${filter === item.value ? ' segmented-filter__button--active' : ''}`}
              type="button"
              onClick={() => setFilter(item.value)}
            >
              {item.label}
            </button>
          ))}
        </div>
      </div>

      <div className="people-summary" aria-live="polite">
        {filteredClasses.length} {filteredClasses.length === 1 ? 'turma' : 'turmas'} | {grouped.planned.length} planejadas | {grouped.history.length} historicas
      </div>

      {isLoading ? (
        <div className="state-panel"><h2>Carregando turmas...</h2><p>Aguarde enquanto os dados sao carregados.</p></div>
      ) : isError ? (
        <div className="state-panel state-panel--error">
          <h2>Nao foi possivel carregar as turmas.</h2>
          <p>Verifique a conexao com o backend e tente novamente.</p>
          <button className="button button--secondary" type="button" onClick={() => void refetch()}>Tentar novamente</button>
        </div>
      ) : filteredClasses.length > 0 ? (
        <DiscipleshipClassesTable classes={filteredClasses} />
      ) : (
        <div className="state-panel"><h2>Nenhuma turma encontrada.</h2><p>Quando houver turmas, elas aparecerao aqui.</p></div>
      )}
    </section>
  )
}

export default DiscipleshipClassesPage
