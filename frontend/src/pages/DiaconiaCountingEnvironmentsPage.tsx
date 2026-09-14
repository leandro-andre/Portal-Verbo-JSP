import { useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { Plus, Save } from 'lucide-react'
import { DiaconiaApiValidationError } from '../api/diaconia'
import { useCan } from '../hooks/useAuth'
import { useCountingEnvironments, useCountingEnvironmentMutations } from '../hooks/useDiaconiaStock'
import type { CountingEnvironment } from '../types/diaconia'

type EnvironmentDraft = {
  name: string
  description: string
}

const emptyDraft: EnvironmentDraft = { name: '', description: '' }

function StatusBadge({ active }: { active: boolean }) {
  return (
    <span className={`status-badge ${active ? 'status-badge--active' : 'status-badge--inactive'}`}>
      <span className="status-badge__dot" aria-hidden="true" />
      {active ? 'Ativo' : 'Inativo'}
    </span>
  )
}

function DiaconiaCountingEnvironmentsPage() {
  const [search, setSearch] = useState('')
  const [status, setStatus] = useState<'ACTIVE' | 'INACTIVE' | 'ALL'>('ACTIVE')
  const filters = useMemo(() => ({ search, status }), [search, status])
  const { data: environments = [], isError, isLoading, refetch } = useCountingEnvironments(filters)
  const mutations = useCountingEnvironmentMutations()
  const canManage = useCan('DIACONIA_COUNTING_MANAGE')
  const [draft, setDraft] = useState<EnvironmentDraft>(emptyDraft)
  const [editingId, setEditingId] = useState<number | null>(null)
  const [editingDraft, setEditingDraft] = useState<EnvironmentDraft>(emptyDraft)
  const [message, setMessage] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)
  const isMutating = mutations.create.isPending || mutations.update.isPending || mutations.deactivate.isPending || mutations.reactivate.isPending

  const editingEnvironment = environments.find((environment) => environment.id === editingId) ?? null

  const handleApiError = (fallback: string, submitError: unknown) => {
    if (submitError instanceof DiaconiaApiValidationError) {
      const firstMessage = Object.values(submitError.fieldErrors).flat()[0]
      setError(firstMessage ?? fallback)
      return
    }
    setError(fallback)
  }

  const handleCreate = async () => {
    setError(null)
    setMessage(null)
    try {
      await mutations.create.mutateAsync(draft)
      setDraft(emptyDraft)
      setMessage('Ambiente criado com sucesso.')
    } catch (submitError) {
      handleApiError('Nao foi possivel criar o ambiente.', submitError)
    }
  }

  const startEdit = (environment: CountingEnvironment) => {
    setEditingId(environment.id)
    setEditingDraft({ name: environment.name, description: environment.description })
    setError(null)
    setMessage(null)
  }

  const handleUpdate = async () => {
    if (!editingEnvironment) return
    setError(null)
    setMessage(null)
    try {
      await mutations.update.mutateAsync({ id: editingEnvironment.id, payload: editingDraft })
      setEditingId(null)
      setMessage('Ambiente atualizado com sucesso.')
    } catch (submitError) {
      handleApiError('Nao foi possivel salvar o ambiente.', submitError)
    }
  }

  const handleLifecycle = async (environment: CountingEnvironment) => {
    setError(null)
    setMessage(null)
    try {
      if (environment.is_active) {
        await mutations.deactivate.mutateAsync(environment.id)
        setMessage('Ambiente inativado com sucesso.')
      } else {
        await mutations.reactivate.mutateAsync(environment.id)
        setMessage('Ambiente reativado com sucesso.')
      }
    } catch {
      setError('Nao foi possivel alterar o status do ambiente.')
    }
  }

  const hasFilters = Boolean(search || status !== 'ACTIVE')

  return (
    <section className="people-page">
      <nav className="breadcrumbs" aria-label="Breadcrumb">
        <Link to="/diaconia">Diaconia</Link>
        <span aria-hidden="true">/</span>
        <strong>Ambientes de Contagem</strong>
      </nav>

      <div className="page-heading">
        <div>
          <h1>Ambientes de Contagem</h1>
          <p className="page-heading__description">Defina os ambientes utilizados pela Diaconia nas contagens de publico.</p>
        </div>
      </div>

      {message ? <div className="form-alert form-alert--success" role="status">{message}</div> : null}
      {error ? <div className="form-alert form-alert--error" role="alert">{error}</div> : null}

      {canManage ? (
        <div className="diaconia-category-form">
          <div className="field-group">
            <label htmlFor="environment-name">Nome *</label>
            <input id="environment-name" type="text" value={draft.name} onChange={(event) => setDraft((current) => ({ ...current, name: event.target.value }))} />
          </div>
          <div className="field-group">
            <label htmlFor="environment-description">Descricao</label>
            <input id="environment-description" type="text" value={draft.description} onChange={(event) => setDraft((current) => ({ ...current, description: event.target.value }))} />
          </div>
          <button className="button button--primary" type="button" disabled={isMutating} onClick={() => void handleCreate()}>
            <Plus size={17} aria-hidden="true" />
            Novo ambiente
          </button>
        </div>
      ) : null}

      <div className="people-toolbar diaconia-stock-filters">
        <label className="people-search" htmlFor="environment-search">
          <span>Buscar</span>
          <input id="environment-search" type="search" placeholder="Nome do ambiente" value={search} onChange={(event) => setSearch(event.target.value)} />
        </label>
        <label className="status-filter" htmlFor="environment-status-filter">
          <span>Status</span>
          <select id="environment-status-filter" value={status} onChange={(event) => setStatus(event.target.value as 'ACTIVE' | 'INACTIVE' | 'ALL')}>
            <option value="ACTIVE">Ativos</option>
            <option value="INACTIVE">Inativos</option>
            <option value="ALL">Todos</option>
          </select>
        </label>
      </div>

      {isLoading ? (
        <div className="state-panel"><h2>Carregando ambientes...</h2></div>
      ) : isError ? (
        <div className="state-panel state-panel--error">
          <h2>Nao foi possivel carregar ambientes.</h2>
          <button className="button button--secondary" type="button" onClick={() => void refetch()}>Tentar novamente</button>
        </div>
      ) : environments.length === 0 ? (
        <div className="state-panel">
          <h2>{hasFilters ? 'Nenhum ambiente encontrado com os filtros aplicados.' : 'Nenhum ambiente de contagem cadastrado.'}</h2>
          <p>{hasFilters ? 'Ajuste os filtros para ampliar a busca.' : 'Cadastre os ambientes que serao usados nas proximas contagens.'}</p>
          {canManage && !hasFilters ? (
            <button className="button button--primary" type="button" onClick={() => document.getElementById('environment-name')?.focus()}>
              <Plus size={17} aria-hidden="true" />
              Cadastrar primeiro ambiente
            </button>
          ) : null}
        </div>
      ) : (
        <div className="table-shell">
          <table className="people-table">
            <thead>
              <tr>
                <th>Ambiente</th>
                <th>Descricao</th>
                <th>Status</th>
                <th aria-label="Acoes" />
              </tr>
            </thead>
            <tbody>
              {environments.map((environment) => {
                const isEditing = editingId === environment.id
                return (
                  <tr key={environment.id}>
                    <td>
                      {isEditing ? (
                        <input className="table-input" value={editingDraft.name} onChange={(event) => setEditingDraft((current) => ({ ...current, name: event.target.value }))} />
                      ) : (
                        <strong>{environment.name}</strong>
                      )}
                    </td>
                    <td>
                      {isEditing ? (
                        <input className="table-input" value={editingDraft.description} onChange={(event) => setEditingDraft((current) => ({ ...current, description: event.target.value }))} />
                      ) : (
                        environment.description || <span className="table-muted">Sem descricao</span>
                      )}
                    </td>
                    <td><StatusBadge active={environment.is_active} /></td>
                    <td>
                      {canManage ? (
                        <div className="table-actions">
                          {isEditing ? (
                            <>
                              <button className="button button--primary" type="button" disabled={isMutating} onClick={() => void handleUpdate()}>
                                <Save size={17} aria-hidden="true" />
                                Salvar
                              </button>
                              <button className="button button--secondary" type="button" onClick={() => setEditingId(null)}>Cancelar</button>
                            </>
                          ) : (
                            <>
                              <button className="button button--secondary" type="button" onClick={() => startEdit(environment)}>Editar</button>
                              <button className="button button--secondary" type="button" disabled={isMutating} onClick={() => void handleLifecycle(environment)}>
                                {environment.is_active ? 'Inativar' : 'Reativar'}
                              </button>
                            </>
                          )}
                        </div>
                      ) : null}
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      )}
    </section>
  )
}

export default DiaconiaCountingEnvironmentsPage
