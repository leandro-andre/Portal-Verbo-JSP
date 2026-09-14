import { Link } from 'react-router-dom'
import { RefreshCcw } from 'lucide-react'
import { useStockMovements } from '../hooks/useDiaconiaStock'

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
  const { data: movements = [], isError, isLoading, refetch } = useStockMovements()

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
          <h2>Nenhuma movimentacao registrada.</h2>
          <p>Entradas e saidas aparecerao aqui depois do primeiro registro.</p>
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
                  <td>{movementQuantitySign(movement.movement_type)}{movement.quantity} {movement.item.unit}</td>
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
