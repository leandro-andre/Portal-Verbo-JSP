import { useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { RefreshCcw } from 'lucide-react'
import { useStockItems, useStockMovements } from '../hooks/useDiaconiaStock'
import type { StockMovementType } from '../types/diaconia'

function formatDateTime(value: string) {
  return new Intl.DateTimeFormat('pt-BR', {
    dateStyle: 'short',
    timeStyle: 'short',
  }).format(new Date(value))
}

function movementQuantitySign(type: string) {
  return type === 'ENTRADA' ? '+' : '-'
}

function DiaconiaStockMovementsPage() {
  const [search, setSearch] = useState('')
  const [item, setItem] = useState('')
  const [type, setType] = useState<'' | StockMovementType>('')
  const filters = useMemo(() => ({ search, item, type }), [item, search, type])
  const { data: movements = [], isError, isLoading, refetch } = useStockMovements(filters)
  const { data: items = [] } = useStockItems({ status: 'ALL' })

  return (
    <section className="people-page">
      <nav className="breadcrumbs" aria-label="Breadcrumb">
        <Link to="/diaconia">Diaconia</Link>
        <span aria-hidden="true">/</span>
        <Link to="/diaconia/estoque">Estoque</Link>
        <span aria-hidden="true">/</span>
        <strong>Movimentacoes</strong>
      </nav>

      <div className="page-heading">
        <div>
          <h1>Movimentacoes</h1>
          <p className="page-heading__description">Historico de entradas e saidas do estoque.</p>
        </div>
      </div>

      <div className="people-toolbar diaconia-stock-filters">
        <label className="people-search" htmlFor="movement-search">
          <span>Buscar</span>
          <input id="movement-search" type="search" placeholder="Nome do item" value={search} onChange={(event) => setSearch(event.target.value)} />
        </label>
        <label className="status-filter" htmlFor="movement-item-filter">
          <span>Item</span>
          <select id="movement-item-filter" value={item} onChange={(event) => setItem(event.target.value)}>
            <option value="">Todos</option>
            {items.map((stockItem) => <option key={stockItem.id} value={stockItem.id}>{stockItem.name}</option>)}
          </select>
        </label>
        <label className="status-filter" htmlFor="movement-type-filter">
          <span>Tipo</span>
          <select id="movement-type-filter" value={type} onChange={(event) => setType(event.target.value as '' | StockMovementType)}>
            <option value="">Todos</option>
            <option value="ENTRADA">Entrada</option>
            <option value="SAIDA">Saida</option>
          </select>
        </label>
      </div>

      {isLoading ? (
        <div className="state-panel"><h2>Carregando movimentacoes...</h2></div>
      ) : isError ? (
        <div className="state-panel state-panel--error">
          <h2>Nao foi possivel carregar movimentacoes.</h2>
          <button className="button button--secondary" type="button" onClick={() => void refetch()}>
            <RefreshCcw size={17} aria-hidden="true" />
            Tentar novamente
          </button>
        </div>
      ) : movements.length === 0 ? (
        <div className="state-panel">
          <h2>{search || item || type ? 'Nenhuma movimentacao encontrada com os filtros aplicados.' : 'Nenhuma movimentacao registrada.'}</h2>
          <p>{search || item || type ? 'Ajuste os filtros para ampliar a busca.' : 'Entradas e saidas aparecerao aqui depois do primeiro registro.'}</p>
        </div>
      ) : (
        <div className="table-shell">
          <table className="people-table">
            <thead>
              <tr>
                <th>Data/Hora</th>
                <th>Item</th>
                <th>Tipo</th>
                <th>Quantidade</th>
                <th>Usuario</th>
                <th>Observacao</th>
              </tr>
            </thead>
            <tbody>
              {movements.map((movement) => (
                <tr key={movement.id}>
                  <td>{formatDateTime(movement.created_at)}</td>
                  <td>{movement.item.name}</td>
                  <td>{movement.movement_type_label}</td>
                  <td>
                    <span className={`diaconia-movement-quantity diaconia-movement-quantity--${movement.movement_type.toLowerCase()}`}>
                      {movementQuantitySign(movement.movement_type)}{movement.quantity} {movement.item.unit}
                    </span>
                  </td>
                  <td>{movement.created_by.display_name}</td>
                  <td>{movement.notes || <span className="table-muted">Sem observacao</span>}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  )
}

export default DiaconiaStockMovementsPage
