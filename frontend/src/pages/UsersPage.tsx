import { useMemo, useState } from 'react'
import { Search, ShieldCheck } from 'lucide-react'
import UsersTable from '../components/users/UsersTable'
import { UserAccessHttpError } from '../api/users'
import { useUsers } from '../hooks/useUsers'
import type { AccessStatus } from '../types/user'

const filters: Array<{ label: string; value: AccessStatus | 'ALL' }> = [
  { label: 'Todos', value: 'ALL' },
  { label: 'Ativos', value: 'ACTIVE' },
  { label: 'Aguardando ativacao', value: 'PENDING_ACTIVATION' },
  { label: 'Bloqueados', value: 'BLOCKED' },
]

function UsersPage() {
  const [statusFilter, setStatusFilter] = useState<AccessStatus | 'ALL'>('ALL')
  const [searchTerm, setSearchTerm] = useState('')
  const { data: users = [], error, isError, isLoading, refetch } = useUsers()
  const isForbidden = error instanceof UserAccessHttpError && error.status === 403

  const filteredUsers = useMemo(() => {
    const normalizedSearch = searchTerm.trim().toLowerCase()
    return users.filter((user) => {
      const matchesStatus = statusFilter === 'ALL' || user.access_status === statusFilter
      const matchesSearch = !normalizedSearch ||
        user.username.toLowerCase().includes(normalizedSearch) ||
        (user.person?.display_name || '').toLowerCase().includes(normalizedSearch)

      return matchesStatus && matchesSearch
    })
  }, [searchTerm, statusFilter, users])

  return (
    <section className="people-page">
      <div className="page-heading">
        <div>
          <h1>Usuarios</h1>
          <p className="page-heading__description">Gerencie os acessos ao Portal.</p>
        </div>
      </div>

      <div className="people-toolbar">
        <label className="search-field">
          <Search className="search-field__icon" size={18} aria-hidden="true" />
          <span className="sr-only">Buscar usuario</span>
          <input
            type="search"
            placeholder="Buscar por pessoa ou usuario"
            value={searchTerm}
            onChange={(event) => setSearchTerm(event.target.value)}
          />
        </label>

        <div className="segmented-filter" aria-label="Filtrar usuarios por status">
          {filters.map((filter) => (
            <button
              className={`segmented-filter__button${statusFilter === filter.value ? ' segmented-filter__button--active' : ''}`}
              key={filter.value}
              type="button"
              onClick={() => setStatusFilter(filter.value)}
            >
              {filter.label}
            </button>
          ))}
        </div>
      </div>

      <span className="people-summary">
        {filteredUsers.length} {filteredUsers.length === 1 ? 'usuario encontrado' : 'usuarios encontrados'}
      </span>

      {isLoading ? (
        <div className="state-panel">
          <h2>Carregando usuarios...</h2>
          <p>Aguarde enquanto os acessos sao carregados.</p>
        </div>
      ) : isError ? (
        <div className="state-panel state-panel--error">
          <ShieldCheck size={26} aria-hidden="true" />
          <h2>{isForbidden ? 'Acesso negado' : 'Nao foi possivel carregar usuarios.'}</h2>
          <p>
            {isForbidden
              ? 'Sua sessao atual nao possui permissao para administrar usuarios.'
              : 'Verifique a conexao com o backend e tente novamente.'}
          </p>
          {!isForbidden ? (
            <button className="button button--secondary" type="button" onClick={() => void refetch()}>
              Tentar novamente
            </button>
          ) : null}
        </div>
      ) : filteredUsers.length === 0 ? (
        <div className="state-panel">
          <h2>Nenhum usuario encontrado</h2>
          <p>Ajuste a busca ou o filtro para ver outros acessos.</p>
        </div>
      ) : (
        <UsersTable users={filteredUsers} />
      )}
    </section>
  )
}

export default UsersPage
