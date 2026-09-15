import { useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { Pencil, Plus } from 'lucide-react'
import { useCan } from '../hooks/useAuth'
import { useInventoryCategories, useInventoryItems } from '../hooks/useDiaconiaInventory'
import type { InventoryItemFilters } from '../types/diaconiaInventory'

function StatusBadge({ active }: { active: boolean }) {
  return (
    <span className={`status-badge ${active ? 'status-badge--active' : 'status-badge--inactive'}`}>
      <span className="status-badge__dot" aria-hidden="true" />
      {active ? 'Ativo' : 'Inativo'}
    </span>
  )
}

function DiaconiaInventoryItemsPage() {
  const canManage = useCan('DIACONIA_INVENTORY_MANAGE')
  const [search, setSearch] = useState('')
  const [category, setCategory] = useState('')
  const [status, setStatus] = useState<InventoryItemFilters['status']>('ACTIVE')
  const filters = useMemo(() => ({ search, category, status }), [search, category, status])
  const { data: items = [], isError, isLoading, refetch } = useInventoryItems(filters)
  const { data: categories = [] } = useInventoryCategories({ status: 'ALL' })
  const hasFilters = Boolean(search || category || status !== 'ACTIVE')

  return (
    <section className="people-page">
      <nav className="breadcrumbs" aria-label="Breadcrumb">
        <Link to="/diaconia">Diaconia</Link>
        <span aria-hidden="true">/</span>
        <Link to="/diaconia/inventario">Inventario</Link>
        <span aria-hidden="true">/</span>
        <strong>Itens</strong>
      </nav>

      <div className="page-heading">
        <div>
          <h1>Itens do Inventario</h1>
          <p className="page-heading__description">Cadastre os tipos de bens patrimoniais controlados pela Diaconia.</p>
        </div>
        {canManage ? (
          <Link className="button button--primary" to="/diaconia/inventario/itens/novo">
            <Plus size={17} aria-hidden="true" />
            Novo item
          </Link>
        ) : null}
      </div>

      <div className="people-toolbar diaconia-stock-filters">
        <label className="people-search" htmlFor="inventory-item-search">
          <span>Buscar</span>
          <input id="inventory-item-search" type="search" placeholder="Nome do item" value={search} onChange={(event) => setSearch(event.target.value)} />
        </label>
        <label className="status-filter" htmlFor="inventory-item-category-filter">
          <span>Categoria</span>
          <select id="inventory-item-category-filter" value={category} onChange={(event) => setCategory(event.target.value)}>
            <option value="">Todas</option>
            {categories.map((itemCategory) => (
              <option key={itemCategory.id} value={itemCategory.id}>{itemCategory.name}</option>
            ))}
          </select>
        </label>
        <label className="status-filter" htmlFor="inventory-item-status-filter">
          <span>Status</span>
          <select id="inventory-item-status-filter" value={status} onChange={(event) => setStatus(event.target.value as InventoryItemFilters['status'])}>
            <option value="ACTIVE">Ativos</option>
            <option value="INACTIVE">Inativos</option>
            <option value="ALL">Todos</option>
          </select>
        </label>
      </div>

      {isLoading ? (
        <div className="state-panel"><h2>Carregando itens...</h2></div>
      ) : isError ? (
        <div className="state-panel state-panel--error">
          <h2>Nao foi possivel carregar itens.</h2>
          <button className="button button--secondary" type="button" onClick={() => void refetch()}>Tentar novamente</button>
        </div>
      ) : items.length === 0 ? (
        <div className="state-panel">
          <h2>{hasFilters ? 'Nenhum item encontrado para os filtros selecionados.' : 'Nenhum item de inventario cadastrado.'}</h2>
          <p>{hasFilters ? 'Ajuste os filtros para ampliar a busca.' : 'Cadastre os bens que farao parte do catalogo operacional.'}</p>
          {canManage && !hasFilters ? (
            <Link className="button button--primary" to="/diaconia/inventario/itens/novo">
              <Plus size={17} aria-hidden="true" />
              Cadastrar primeiro item
            </Link>
          ) : null}
        </div>
      ) : (
        <>
          <div className="table-shell diaconia-inventory-items-table">
            <table className="people-table">
              <thead>
                <tr>
                  <th>Item</th>
                  <th>Categoria</th>
                  <th>Status</th>
                  <th aria-label="Acoes" />
                </tr>
              </thead>
              <tbody>
                {items.map((item) => (
                  <tr key={item.id}>
                    <td>
                      <strong>{item.name}</strong>
                      {item.description ? <span className="table-muted">{item.description}</span> : null}
                    </td>
                    <td>{item.category.name}</td>
                    <td><StatusBadge active={item.is_active} /></td>
                    <td>
                      {canManage ? (
                        <div className="table-actions">
                          <Link className="button button--secondary" to={`/diaconia/inventario/itens/${item.id}/editar`}>
                            <Pencil size={17} aria-hidden="true" />
                            Editar
                          </Link>
                        </div>
                      ) : null}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div className="diaconia-counting-card-list">
            {items.map((item) => (
              <article className="diaconia-counting-history-card" key={item.id}>
                <div>
                  <h2>{item.name}</h2>
                  <p>{item.category.name}</p>
                  <span>{item.is_active ? 'Ativo' : 'Inativo'}</span>
                </div>
                {canManage ? (
                  <Link className="button button--secondary" to={`/diaconia/inventario/itens/${item.id}/editar`}>
                    <Pencil size={17} aria-hidden="true" />
                    Editar
                  </Link>
                ) : null}
              </article>
            ))}
          </div>
        </>
      )}
    </section>
  )
}

export default DiaconiaInventoryItemsPage
