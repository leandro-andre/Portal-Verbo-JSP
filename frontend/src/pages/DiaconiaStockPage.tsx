import { useMemo, useState } from 'react'
import { Link, useLocation } from 'react-router-dom'
import { FolderTree, History, Minus, Plus, RefreshCcw } from 'lucide-react'
import { DiaconiaHttpError } from '../api/diaconia'
import { useCan } from '../hooks/useAuth'
import { useStockCategories, useStockItems, useStockSummary } from '../hooks/useDiaconiaStock'
import type { StockStatus } from '../types/diaconia'

function StockStatusBadge({ active }: { active: boolean }) {
  return (
    <span className={`status-badge ${active ? 'status-badge--active' : 'status-badge--inactive'}`}>
      <span className="status-badge__dot" aria-hidden="true" />
      {active ? 'Ativo' : 'Inativo'}
    </span>
  )
}

function StockSituationBadge({ status, label }: { status: StockStatus; label: string }) {
  const className = {
    NORMAL: 'diaconia-stock-situation--normal',
    LOW_STOCK: 'diaconia-stock-situation--low',
    WITHOUT_MINIMUM: 'diaconia-stock-situation--none',
    INACTIVE: 'diaconia-stock-situation--inactive',
  }[status]

  return (
    <span className={`status-badge diaconia-stock-situation ${className}`}>
      <span className="status-badge__dot" aria-hidden="true" />
      {label}
    </span>
  )
}

function minimumStockLabel(value: number) {
  return value === 0 ? 'Sem controle' : String(value)
}

function DiaconiaStockPage() {
  const location = useLocation()
  const [search, setSearch] = useState('')
  const [category, setCategory] = useState('')
  const [stockStatus, setStockStatus] = useState<'' | StockStatus>('')
  const [status, setStatus] = useState<'ACTIVE' | 'INACTIVE' | 'ALL'>('ACTIVE')
  const itemFilters = useMemo(
    () => ({ search, category, stockStatus, status }),
    [category, search, status, stockStatus],
  )
  const { data: items = [], error, isError, isLoading, refetch } = useStockItems(itemFilters)
  const { data: categories = [] } = useStockCategories()
  const { data: summary } = useStockSummary()
  const canManage = useCan('DIACONIA_STOCK_MANAGE')
  const successMessage = (location.state as { successMessage?: string } | null)?.successMessage ?? null
  const isForbidden = error instanceof DiaconiaHttpError && error.status === 403

  return (
    <section className="people-page">
      <div className="page-heading">
        <div>
          <h1>Estoque</h1>
          <p className="page-heading__description">Controle dos materiais armazenados pela Diaconia</p>
        </div>
        <div className="diaconia-stock-actions">
          <Link className="button button--secondary" to="/diaconia/estoque/categorias">
            <FolderTree size={17} aria-hidden="true" />
            Categorias
          </Link>
          <Link className="button button--secondary" to="/diaconia/estoque/movimentacoes">
            <History size={17} aria-hidden="true" />
            Movimentacoes
          </Link>
          {canManage ? (
            <>
              <Link className="button button--secondary" to="/diaconia/estoque/saida">
                <Minus size={17} aria-hidden="true" />
                Nova saida
              </Link>
              <Link className="button button--secondary" to="/diaconia/estoque/entrada">
                <Plus size={17} aria-hidden="true" />
                Nova entrada
              </Link>
              <Link className="button button--primary" to="/diaconia/estoque/novo">
                <Plus size={17} aria-hidden="true" />
                Novo item
              </Link>
            </>
          ) : null}
        </div>
      </div>

      {successMessage ? <div className="form-alert form-alert--success" role="status">{successMessage}</div> : null}

      <div className="diaconia-stock-metrics">
        <button className="diaconia-stock-metric" type="button" onClick={() => { setStatus('ACTIVE'); setStockStatus('') }}>
          <span>Itens ativos</span>
          <strong>{summary?.active_items ?? '-'}</strong>
        </button>
        <button className="diaconia-stock-metric" type="button" onClick={() => { setStatus('ACTIVE'); setStockStatus('LOW_STOCK') }}>
          <span>Abaixo do minimo</span>
          <strong>{summary?.low_stock_items ?? '-'}</strong>
        </button>
        <button className="diaconia-stock-metric" type="button" onClick={() => { setStatus('ACTIVE'); setStockStatus('WITHOUT_MINIMUM') }}>
          <span>Sem controle minimo</span>
          <strong>{summary?.without_minimum_control ?? '-'}</strong>
        </button>
      </div>

      <section className="diaconia-replenishment">
        <div className="diaconia-replenishment__header">
          <div>
            <h2>Itens que precisam de reposicao</h2>
            <p>Itens ativos com saldo menor ou igual ao estoque minimo.</p>
          </div>
          <button className="button button--secondary" type="button" onClick={() => { setStatus('ACTIVE'); setStockStatus('LOW_STOCK') }}>
            Ver itens para reposicao
          </button>
        </div>
        {summary?.replenishment_items.length ? (
          <div className="table-shell diaconia-replenishment__table">
            <table className="people-table">
              <thead>
                <tr>
                  <th>Item</th>
                  <th>Categoria</th>
                  <th>Saldo</th>
                  <th>Minimo</th>
                  <th>Unidade</th>
                </tr>
              </thead>
              <tbody>
                {summary.replenishment_items.map((item) => (
                  <tr key={item.id}>
                    <td>{item.name}</td>
                    <td>{item.category.name}</td>
                    <td>{item.current_stock}</td>
                    <td>{item.minimum_stock}</td>
                    <td>{item.unit}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <p className="diaconia-replenishment__empty">Nenhum item precisa de reposicao no momento.</p>
        )}
      </section>

      <div className="people-toolbar diaconia-stock-filters">
        <label className="people-search" htmlFor="stock-search">
          <span>Buscar</span>
          <input id="stock-search" type="search" placeholder="Nome do item" value={search} onChange={(event) => setSearch(event.target.value)} />
        </label>
        <label className="status-filter" htmlFor="stock-category-filter">
          <span>Categoria</span>
          <select id="stock-category-filter" value={category} onChange={(event) => setCategory(event.target.value)}>
            <option value="">Todas</option>
            {categories.map((item) => <option key={item.id} value={item.id}>{item.name}</option>)}
          </select>
        </label>
        <label className="status-filter" htmlFor="stock-situation-filter">
          <span>Situacao</span>
          <select id="stock-situation-filter" value={stockStatus} onChange={(event) => setStockStatus(event.target.value as '' | StockStatus)}>
            <option value="">Todos</option>
            <option value="NORMAL">Normal</option>
            <option value="LOW_STOCK">Estoque baixo</option>
            <option value="WITHOUT_MINIMUM">Sem controle</option>
          </select>
        </label>
        <label className="status-filter" htmlFor="stock-status-filter">
          <span>Status</span>
          <select id="stock-status-filter" value={status} onChange={(event) => setStatus(event.target.value as 'ACTIVE' | 'INACTIVE' | 'ALL')}>
            <option value="ACTIVE">Ativos</option>
            <option value="INACTIVE">Inativos</option>
            <option value="ALL">Todos</option>
          </select>
        </label>
      </div>

      {isLoading ? (
        <div className="state-panel">
          <h2>Carregando itens...</h2>
          <p>Aguarde enquanto buscamos os dados.</p>
        </div>
      ) : isError ? (
        <div className="state-panel state-panel--error">
          <h2>{isForbidden ? 'Acesso negado' : 'Nao foi possivel carregar o estoque.'}</h2>
          <p>{isForbidden ? 'Sua sessao atual nao possui permissao para visualizar a Diaconia.' : 'Verifique a conexao com o backend e tente novamente.'}</p>
          {!isForbidden ? (
            <button className="button button--secondary" type="button" onClick={() => void refetch()}>
              <RefreshCcw size={17} aria-hidden="true" />
              Tentar novamente
            </button>
          ) : null}
        </div>
      ) : items.length === 0 ? (
        <div className="state-panel">
          <h2>{search || category || stockStatus || status !== 'ACTIVE' ? 'Nenhum item encontrado com os filtros aplicados.' : 'Nenhum item cadastrado no estoque.'}</h2>
          <p>{search || category || stockStatus || status !== 'ACTIVE' ? 'Ajuste os filtros para ampliar a busca.' : 'Cadastre os materiais que serao controlados pela Diaconia.'}</p>
          {canManage && !search && !category && !stockStatus && status === 'ACTIVE' ? (
            <Link className="button button--primary" to="/diaconia/estoque/novo">
              <Plus size={17} aria-hidden="true" />
              Cadastrar primeiro item
            </Link>
          ) : null}
        </div>
      ) : (
        <div className="table-shell">
          <table className="people-table">
            <thead>
              <tr>
                <th>Item</th>
                <th>Categoria</th>
                <th>Unidade</th>
                <th>Saldo</th>
                <th>Estoque minimo</th>
                <th>Situacao</th>
                <th>Status</th>
                <th aria-label="Acao" />
              </tr>
            </thead>
            <tbody>
              {items.map((item) => (
                <tr key={item.id}>
                  <td>
                    <strong>{item.name}</strong>
                    {item.notes ? <span className="table-muted">{item.notes}</span> : null}
                  </td>
                  <td>{item.category.name}</td>
                  <td>{item.unit}</td>
                  <td>{item.current_stock}</td>
                  <td>{minimumStockLabel(item.minimum_stock)}</td>
                  <td><StockSituationBadge status={item.stock_status} label={item.stock_status_label} /></td>
                  <td><StockStatusBadge active={item.is_active} /></td>
                  <td>
                    {canManage ? (
                      <Link className="button button--secondary" to={`/diaconia/estoque/${item.id}/editar`}>
                        Editar
                      </Link>
                    ) : null}
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

export default DiaconiaStockPage
