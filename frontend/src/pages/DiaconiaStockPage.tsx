import { Link, useLocation } from 'react-router-dom'
import { FolderTree, History, Minus, Plus, RefreshCcw } from 'lucide-react'
import { DiaconiaHttpError } from '../api/diaconia'
import { useCan } from '../hooks/useAuth'
import { useStockItems } from '../hooks/useDiaconiaStock'

function StockStatusBadge({ active }: { active: boolean }) {
  return (
    <span className={`status-badge ${active ? 'status-badge--active' : 'status-badge--inactive'}`}>
      <span className="status-badge__dot" aria-hidden="true" />
      {active ? 'Ativo' : 'Inativo'}
    </span>
  )
}

function minimumStockLabel(value: number) {
  return value === 0 ? 'Sem controle' : String(value)
}

function DiaconiaStockPage() {
  const location = useLocation()
  const { data: items = [], error, isError, isLoading, refetch } = useStockItems()
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
          <h2>Nenhum item cadastrado.</h2>
          <p>Cadastre os materiais que serao controlados pela Diaconia.</p>
          {canManage ? (
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
