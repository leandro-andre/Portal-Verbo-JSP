import { useMemo, useState } from 'react'
import { Building2, Plus } from 'lucide-react'
import { Link, useLocation } from 'react-router-dom'
import { DepartmentHttpError } from '../api/departments'
import { useCan } from '../hooks/useAuth'
import { useDepartments } from '../hooks/useDepartments'

type DepartmentFilter = 'ALL' | 'ACTIVE' | 'INACTIVE'

const filters: Array<{ label: string; value: DepartmentFilter }> = [
  { label: 'Todos', value: 'ALL' },
  { label: 'Ativos', value: 'ACTIVE' },
  { label: 'Inativos', value: 'INACTIVE' },
]

function DepartmentStatusBadge({ ativo }: { ativo: boolean }) {
  return (
    <span className={`status-badge ${ativo ? 'person-status-badge--active' : 'person-status-badge--inactive'}`}>
      <span className="status-badge__dot" aria-hidden="true" />
      {ativo ? 'Ativo' : 'Inativo'}
    </span>
  )
}

function DepartmentsPage() {
  const location = useLocation()
  const [filter, setFilter] = useState<DepartmentFilter>('ALL')
  const [search, setSearch] = useState('')
  const { data: departments = [], error, isError, isLoading, refetch } = useDepartments()
  const canCreate = useCan('DEPARTMENT_CREATE')
  const successMessage = (location.state as { successMessage?: string } | null)?.successMessage ?? null
  const isForbidden = error instanceof DepartmentHttpError && error.status === 403
  const normalizedSearch = search.trim().toLowerCase()
  const filteredDepartments = useMemo(
    () =>
      departments.filter((department) => {
        if (filter === 'ACTIVE' && !department.ativo) {
          return false
        }
        if (filter === 'INACTIVE' && department.ativo) {
          return false
        }
        if (!normalizedSearch) {
          return true
        }
        return (
          department.nome.toLowerCase().includes(normalizedSearch) ||
          department.codigo.toLowerCase().includes(normalizedSearch) ||
          department.descricao.toLowerCase().includes(normalizedSearch)
        )
      }),
    [departments, filter, normalizedSearch],
  )

  return (
    <section className="people-page">
      <div className="page-heading">
        <div>
          <h1>Departamentos</h1>
          <p className="page-heading__description">Gerencie os departamentos da igreja.</p>
        </div>
        {canCreate ? (
          <Link className="button button--primary" to="/departamentos/novo">
            <Plus size={17} aria-hidden="true" />
            Novo departamento
          </Link>
        ) : null}
      </div>

      {successMessage ? (
        <div className="form-alert form-alert--success" role="status">
          {successMessage}
        </div>
      ) : null}

      <div className="people-toolbar">
        <label className="people-search" htmlFor="department-search">
          <span>Buscar</span>
          <input
            id="department-search"
            type="search"
            placeholder="Nome, codigo ou descricao"
            value={search}
            onChange={(event) => setSearch(event.target.value)}
          />
        </label>
        <div className="segmented-filter" aria-label="Filtrar departamentos">
          {filters.map((item) => (
            <button
              className={`segmented-filter__button${filter === item.value ? ' segmented-filter__button--active' : ''}`}
              key={item.value}
              type="button"
              onClick={() => setFilter(item.value)}
            >
              {item.label}
            </button>
          ))}
        </div>
      </div>

      {isLoading ? (
        <div className="state-panel">
          <h2>Carregando departamentos...</h2>
          <p>Aguarde enquanto buscamos os dados.</p>
        </div>
      ) : isError ? (
        <div className="state-panel state-panel--error">
          <Building2 size={26} aria-hidden="true" />
          <h2>{isForbidden ? 'Acesso negado' : 'Nao foi possivel carregar departamentos.'}</h2>
          <p>
            {isForbidden
              ? 'Sua sessao atual nao possui permissao para visualizar departamentos.'
              : 'Verifique a conexao com o backend e tente novamente.'}
          </p>
          {!isForbidden ? (
            <button className="button button--secondary" type="button" onClick={() => void refetch()}>
              Tentar novamente
            </button>
          ) : null}
        </div>
      ) : filteredDepartments.length === 0 ? (
        <div className="state-panel">
          <h2>Nenhum departamento encontrado</h2>
          <p>Ajuste os filtros ou cadastre um novo departamento.</p>
        </div>
      ) : (
        <div className="table-shell">
          <table className="people-table">
            <thead>
              <tr>
                <th>Departamento</th>
                <th>Codigo</th>
                <th>Status</th>
                <th aria-label="Acao" />
              </tr>
            </thead>
            <tbody>
              {filteredDepartments.map((department) => (
                <tr key={department.id}>
                  <td>
                    <Link className="person-name-link" to={`/departamentos/${department.id}`}>
                      {department.nome}
                    </Link>
                    {department.descricao ? <span className="table-muted">{department.descricao}</span> : null}
                  </td>
                  <td>{department.codigo}</td>
                  <td><DepartmentStatusBadge ativo={department.ativo} /></td>
                  <td>
                    <Link className="button button--secondary" to={`/departamentos/${department.id}`}>
                      Ver
                    </Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  )
}

export default DepartmentsPage
