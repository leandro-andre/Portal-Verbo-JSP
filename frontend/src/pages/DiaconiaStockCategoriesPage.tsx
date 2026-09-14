import { useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { Plus, Save } from 'lucide-react'
import { DiaconiaApiValidationError } from '../api/diaconia'
import { useCan } from '../hooks/useAuth'
import { useStockCategories, useStockCategoryMutations } from '../hooks/useDiaconiaStock'
import type { StockCategory } from '../types/diaconia'

type CategoryDraft = {
  name: string
  description: string
}

const emptyDraft: CategoryDraft = { name: '', description: '' }

function DiaconiaStockCategoriesPage() {
  const { data: categories = [], isError, isLoading, refetch } = useStockCategories()
  const mutations = useStockCategoryMutations()
  const canManage = useCan('DIACONIA_STOCK_MANAGE')
  const [draft, setDraft] = useState<CategoryDraft>(emptyDraft)
  const [editingId, setEditingId] = useState<number | null>(null)
  const [editingDraft, setEditingDraft] = useState<CategoryDraft>(emptyDraft)
  const [message, setMessage] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)
  const isMutating = mutations.create.isPending || mutations.update.isPending || mutations.deactivate.isPending || mutations.reactivate.isPending

  const editingCategory = useMemo(
    () => categories.find((category) => category.id === editingId) ?? null,
    [categories, editingId],
  )

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
      setMessage('Categoria criada com sucesso.')
    } catch (submitError) {
      handleApiError('Nao foi possivel criar a categoria.', submitError)
    }
  }

  const startEdit = (category: StockCategory) => {
    setEditingId(category.id)
    setEditingDraft({ name: category.name, description: category.description })
    setError(null)
    setMessage(null)
  }

  const handleUpdate = async () => {
    if (!editingCategory) return
    setError(null)
    setMessage(null)
    try {
      await mutations.update.mutateAsync({ id: editingCategory.id, payload: editingDraft })
      setEditingId(null)
      setMessage('Categoria atualizada com sucesso.')
    } catch (submitError) {
      handleApiError('Nao foi possivel salvar a categoria.', submitError)
    }
  }

  const handleLifecycle = async (category: StockCategory) => {
    setError(null)
    setMessage(null)
    try {
      if (category.is_active) {
        await mutations.deactivate.mutateAsync(category.id)
        setMessage('Categoria inativada com sucesso.')
      } else {
        await mutations.reactivate.mutateAsync(category.id)
        setMessage('Categoria reativada com sucesso.')
      }
    } catch {
      setError('Nao foi possivel alterar o status da categoria.')
    }
  }

  return (
    <section className="people-page">
      <nav className="breadcrumbs" aria-label="Breadcrumb">
        <Link to="/diaconia">Diaconia</Link>
        <span aria-hidden="true">/</span>
        <Link to="/diaconia/estoque">Estoque</Link>
        <span aria-hidden="true">/</span>
        <strong>Categorias</strong>
      </nav>

      <div className="page-heading">
        <div>
          <h1>Categorias</h1>
          <p className="page-heading__description">Organize os materiais controlados no estoque.</p>
        </div>
      </div>

      {message ? <div className="form-alert form-alert--success" role="status">{message}</div> : null}
      {error ? <div className="form-alert form-alert--error" role="alert">{error}</div> : null}

      {canManage ? (
        <div className="diaconia-category-form">
          <div className="field-group">
            <label htmlFor="category-name">Nome *</label>
            <input id="category-name" type="text" value={draft.name} onChange={(event) => setDraft((current) => ({ ...current, name: event.target.value }))} />
          </div>
          <div className="field-group">
            <label htmlFor="category-description">Descricao</label>
            <input id="category-description" type="text" value={draft.description} onChange={(event) => setDraft((current) => ({ ...current, description: event.target.value }))} />
          </div>
          <button className="button button--primary" type="button" disabled={isMutating} onClick={() => void handleCreate()}>
            <Plus size={17} aria-hidden="true" />
            Nova categoria
          </button>
        </div>
      ) : null}

      {isLoading ? (
        <div className="state-panel"><h2>Carregando categorias...</h2></div>
      ) : isError ? (
        <div className="state-panel state-panel--error">
          <h2>Nao foi possivel carregar categorias.</h2>
          <button className="button button--secondary" type="button" onClick={() => void refetch()}>Tentar novamente</button>
        </div>
      ) : categories.length === 0 ? (
        <div className="state-panel">
          <h2>Nenhuma categoria cadastrada.</h2>
          <p>Cadastre categorias para organizar os itens de estoque.</p>
        </div>
      ) : (
        <div className="table-shell">
          <table className="people-table">
            <thead>
              <tr>
                <th>Categoria</th>
                <th>Descricao</th>
                <th>Status</th>
                <th aria-label="Acoes" />
              </tr>
            </thead>
            <tbody>
              {categories.map((category) => {
                const isEditing = editingId === category.id
                return (
                  <tr key={category.id}>
                    <td>
                      {isEditing ? (
                        <input className="table-input" value={editingDraft.name} onChange={(event) => setEditingDraft((current) => ({ ...current, name: event.target.value }))} />
                      ) : (
                        <strong>{category.name}</strong>
                      )}
                    </td>
                    <td>
                      {isEditing ? (
                        <input className="table-input" value={editingDraft.description} onChange={(event) => setEditingDraft((current) => ({ ...current, description: event.target.value }))} />
                      ) : (
                        category.description || <span className="table-muted">Sem descricao</span>
                      )}
                    </td>
                    <td>
                      <span className={`status-badge ${category.is_active ? 'status-badge--active' : 'status-badge--inactive'}`}>
                        <span className="status-badge__dot" aria-hidden="true" />
                        {category.is_active ? 'Ativa' : 'Inativa'}
                      </span>
                    </td>
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
                              <button className="button button--secondary" type="button" onClick={() => startEdit(category)}>Editar</button>
                              <button className="button button--secondary" type="button" disabled={isMutating} onClick={() => void handleLifecycle(category)}>
                                {category.is_active ? 'Inativar' : 'Reativar'}
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

export default DiaconiaStockCategoriesPage
