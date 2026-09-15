import { useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { Plus, Save } from 'lucide-react'
import { DiaconiaApiValidationError } from '../api/diaconia'
import { useCan } from '../hooks/useAuth'
import {
  useInventoryCategories,
  useInventoryCategoryMutations,
  useInventoryLocations,
  useInventoryLocationMutations,
} from '../hooks/useDiaconiaInventory'
import type { InventoryCategory, InventoryFilters, InventoryLocation } from '../types/diaconiaInventory'

type RegistryKind = 'categories' | 'locations'
type RegistryItem = InventoryCategory | InventoryLocation
type RegistryDraft = { name: string; description: string }

const emptyDraft: RegistryDraft = { name: '', description: '' }

function StatusBadge({ active }: { active: boolean }) {
  return (
    <span className={`status-badge ${active ? 'status-badge--active' : 'status-badge--inactive'}`}>
      <span className="status-badge__dot" aria-hidden="true" />
      {active ? 'Ativo' : 'Inativo'}
    </span>
  )
}

function DiaconiaInventoryRegistryPage({ kind }: { kind: RegistryKind }) {
  const [search, setSearch] = useState('')
  const [status, setStatus] = useState<InventoryFilters['status']>('ACTIVE')
  const filters = useMemo(() => ({ search, status }), [search, status])
  const categoriesQuery = useInventoryCategories(kind === 'categories' ? filters : undefined)
  const locationsQuery = useInventoryLocations(kind === 'locations' ? filters : undefined)
  const categoryMutations = useInventoryCategoryMutations()
  const locationMutations = useInventoryLocationMutations()
  const canManage = useCan('DIACONIA_INVENTORY_MANAGE')
  const [draft, setDraft] = useState<RegistryDraft>(emptyDraft)
  const [editingId, setEditingId] = useState<number | null>(null)
  const [editingDraft, setEditingDraft] = useState<RegistryDraft>(emptyDraft)
  const [message, setMessage] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)

  const isCategory = kind === 'categories'
  const query = isCategory ? categoriesQuery : locationsQuery
  const mutations = isCategory ? categoryMutations : locationMutations
  const items = (query.data ?? []) as RegistryItem[]
  const editingItem = items.find((item) => item.id === editingId) ?? null
  const isMutating = mutations.create.isPending || mutations.update.isPending || mutations.deactivate.isPending || mutations.reactivate.isPending
  const hasFilters = Boolean(search || status !== 'ACTIVE')
  const labels = isCategory
    ? {
      title: 'Categorias de Inventario',
      singular: 'categoria',
      description: 'Organize os tipos de bens do inventario.',
      create: 'Nova categoria',
      empty: 'Nenhuma categoria de inventario cadastrada.',
      first: 'Cadastrar primeira categoria',
      searchPlaceholder: 'Nome da categoria',
    }
    : {
      title: 'Locais de Inventario',
      singular: 'local',
      description: 'Defina onde os bens da igreja podem estar alocados.',
      create: 'Novo local',
      empty: 'Nenhum local de inventario cadastrado.',
      first: 'Cadastrar primeiro local',
      searchPlaceholder: 'Nome do local',
    }

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
      setMessage(`${labels.singular[0].toUpperCase()}${labels.singular.slice(1)} criado com sucesso.`)
    } catch (submitError) {
      handleApiError(`Nao foi possivel criar o ${labels.singular}.`, submitError)
    }
  }

  const startEdit = (item: RegistryItem) => {
    setEditingId(item.id)
    setEditingDraft({ name: item.name, description: item.description })
    setError(null)
    setMessage(null)
  }

  const handleUpdate = async () => {
    if (!editingItem) return
    setError(null)
    setMessage(null)
    try {
      await mutations.update.mutateAsync({ id: editingItem.id, payload: editingDraft })
      setEditingId(null)
      setMessage(`${labels.singular[0].toUpperCase()}${labels.singular.slice(1)} atualizado com sucesso.`)
    } catch (submitError) {
      handleApiError(`Nao foi possivel salvar o ${labels.singular}.`, submitError)
    }
  }

  const handleLifecycle = async (item: RegistryItem) => {
    setError(null)
    setMessage(null)
    try {
      if (item.is_active) {
        await mutations.deactivate.mutateAsync(item.id)
        setMessage(`${labels.singular[0].toUpperCase()}${labels.singular.slice(1)} inativado com sucesso.`)
      } else {
        await mutations.reactivate.mutateAsync(item.id)
        setMessage(`${labels.singular[0].toUpperCase()}${labels.singular.slice(1)} reativado com sucesso.`)
      }
    } catch {
      setError(`Nao foi possivel alterar o status do ${labels.singular}.`)
    }
  }

  return (
    <section className="people-page">
      <nav className="breadcrumbs" aria-label="Breadcrumb">
        <Link to="/diaconia">Diaconia</Link>
        <span aria-hidden="true">/</span>
        <Link to="/diaconia/inventario">Inventario</Link>
        <span aria-hidden="true">/</span>
        <strong>{labels.title}</strong>
      </nav>

      <div className="page-heading">
        <div>
          <h1>{labels.title}</h1>
          <p className="page-heading__description">{labels.description}</p>
        </div>
      </div>

      {message ? <div className="form-alert form-alert--success" role="status">{message}</div> : null}
      {error ? <div className="form-alert form-alert--error" role="alert">{error}</div> : null}

      {canManage ? (
        <div className="diaconia-category-form">
          <div className="field-group">
            <label htmlFor="inventory-name">Nome *</label>
            <input id="inventory-name" type="text" value={draft.name} onChange={(event) => setDraft((current) => ({ ...current, name: event.target.value }))} />
          </div>
          <div className="field-group">
            <label htmlFor="inventory-description">Descricao</label>
            <input id="inventory-description" type="text" value={draft.description} onChange={(event) => setDraft((current) => ({ ...current, description: event.target.value }))} />
          </div>
          <button className="button button--primary" type="button" disabled={isMutating} onClick={() => void handleCreate()}>
            <Plus size={17} aria-hidden="true" />
            {labels.create}
          </button>
        </div>
      ) : null}

      <div className="people-toolbar diaconia-stock-filters">
        <label className="people-search" htmlFor="inventory-search">
          <span>Buscar</span>
          <input id="inventory-search" type="search" placeholder={labels.searchPlaceholder} value={search} onChange={(event) => setSearch(event.target.value)} />
        </label>
        <label className="status-filter" htmlFor="inventory-status-filter">
          <span>Status</span>
          <select id="inventory-status-filter" value={status} onChange={(event) => setStatus(event.target.value as InventoryFilters['status'])}>
            <option value="ACTIVE">Ativos</option>
            <option value="INACTIVE">Inativos</option>
            <option value="ALL">Todos</option>
          </select>
        </label>
      </div>

      {query.isLoading ? (
        <div className="state-panel"><h2>Carregando registros...</h2></div>
      ) : query.isError ? (
        <div className="state-panel state-panel--error">
          <h2>Nao foi possivel carregar registros.</h2>
          <button className="button button--secondary" type="button" onClick={() => void query.refetch()}>Tentar novamente</button>
        </div>
      ) : items.length === 0 ? (
        <div className="state-panel">
          <h2>{hasFilters ? 'Nenhum registro encontrado com os filtros aplicados.' : labels.empty}</h2>
          <p>{hasFilters ? 'Ajuste os filtros para ampliar a busca.' : 'Crie o primeiro cadastro para estruturar o inventario.'}</p>
          {canManage && !hasFilters ? (
            <button className="button button--primary" type="button" onClick={() => document.getElementById('inventory-name')?.focus()}>
              <Plus size={17} aria-hidden="true" />
              {labels.first}
            </button>
          ) : null}
        </div>
      ) : (
        <div className="table-shell">
          <table className="people-table">
            <thead>
              <tr>
                <th>{isCategory ? 'Categoria' : 'Local'}</th>
                <th>Descricao</th>
                <th>Status</th>
                <th aria-label="Acoes" />
              </tr>
            </thead>
            <tbody>
              {items.map((item) => {
                const isEditing = editingId === item.id
                return (
                  <tr key={item.id}>
                    <td>
                      {isEditing ? (
                        <input className="table-input" value={editingDraft.name} onChange={(event) => setEditingDraft((current) => ({ ...current, name: event.target.value }))} />
                      ) : (
                        <strong>{item.name}</strong>
                      )}
                    </td>
                    <td>
                      {isEditing ? (
                        <input className="table-input" value={editingDraft.description} onChange={(event) => setEditingDraft((current) => ({ ...current, description: event.target.value }))} />
                      ) : (
                        item.description || <span className="table-muted">Sem descricao</span>
                      )}
                    </td>
                    <td><StatusBadge active={item.is_active} /></td>
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
                              <button className="button button--secondary" type="button" onClick={() => startEdit(item)}>Editar</button>
                              <button className="button button--secondary" type="button" disabled={isMutating} onClick={() => void handleLifecycle(item)}>
                                {item.is_active ? 'Inativar' : 'Reativar'}
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

export default DiaconiaInventoryRegistryPage
