import { Eye, Plus } from 'lucide-react'
import { Link } from 'react-router-dom'
import { useMemo, useState } from 'react'
import { useCan } from '../hooks/useAuth'
import { useInventoryCounts } from '../hooks/useDiaconiaInventory'

function formatDate(value: string) {
  const [year, month, day] = value.split('-')
  if (!year || !month || !day) return value
  return `${day}/${month}/${year}`
}

function DiaconiaInventoryCountsPage() {
  const canManage = useCan('DIACONIA_INVENTORY_MANAGE')
  const [dateFrom, setDateFrom] = useState('')
  const [dateTo, setDateTo] = useState('')
  const filters = useMemo(
    () => ({
      ...(dateFrom ? { date_from: dateFrom } : {}),
      ...(dateTo ? { date_to: dateTo } : {}),
    }),
    [dateFrom, dateTo],
  )
  const { data: counts = [], isError, isLoading, refetch } = useInventoryCounts(filters)

  return (
    <section className="people-page">
      <nav className="breadcrumbs" aria-label="Breadcrumb">
        <Link to="/diaconia">Diaconia</Link>
        <span aria-hidden="true">/</span>
        <Link to="/diaconia/inventario">Inventario</Link>
        <span aria-hidden="true">/</span>
        <strong>Contagens</strong>
      </nav>

      <div className="page-heading">
        <div>
          <h1>Contagens de Inventario</h1>
          <p className="page-heading__description">Consulte os snapshots fisicos registrados para o inventario da igreja.</p>
        </div>
        <div className="diaconia-stock-actions">
          {canManage ? (
            <Link className="button button--primary" to="/diaconia/inventario/contagens/nova">
              <Plus size={17} aria-hidden="true" />
              Nova contagem
            </Link>
          ) : null}
          <Link className="button button--secondary" to="/diaconia/inventario">Voltar</Link>
        </div>
      </div>

      <div className="diaconia-counting-form">
        <div className="form-grid">
          <div className="field-group">
            <label htmlFor="inventory-count-date-from">Data inicial</label>
            <input id="inventory-count-date-from" type="date" value={dateFrom} onChange={(event) => setDateFrom(event.target.value)} />
          </div>
          <div className="field-group">
            <label htmlFor="inventory-count-date-to">Data final</label>
            <input id="inventory-count-date-to" type="date" value={dateTo} onChange={(event) => setDateTo(event.target.value)} />
          </div>
        </div>
      </div>

      {isLoading ? (
        <div className="state-panel"><h2>Carregando contagens...</h2></div>
      ) : isError ? (
        <div className="state-panel state-panel--error">
          <h2>Nao foi possivel carregar as contagens.</h2>
          <button className="button button--secondary" type="button" onClick={() => void refetch()}>Tentar novamente</button>
        </div>
      ) : counts.length === 0 ? (
        <div className="state-panel">
          <h2>Nenhuma contagem encontrada.</h2>
          <p>Registre uma nova contagem ou ajuste o periodo filtrado.</p>
        </div>
      ) : (
        <>
          <div className="table-shell inventory-count-history-table">
            <table className="people-table">
              <thead>
                <tr>
                  <th>Data</th>
                  <th>Responsavel</th>
                  <th>Itens</th>
                  <th>Locais</th>
                  <th>Registrada em</th>
                  <th className="people-table__actions-header">Acoes</th>
                </tr>
              </thead>
              <tbody>
                {counts.map((count) => (
                  <tr key={count.id}>
                    <td>{formatDate(count.date)}</td>
                    <td>{count.created_by.display_name}</td>
                    <td>{count.items_count}</td>
                    <td>{count.locations_count}</td>
                    <td>{new Date(count.created_at).toLocaleString('pt-BR')}</td>
                    <td>
                      <div className="table-actions">
                        <Link className="button button--secondary" to={`/diaconia/inventario/contagens/${count.id}`}>
                          <Eye size={16} aria-hidden="true" />
                          Ver
                        </Link>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div className="diaconia-counting-card-list inventory-count-history-cards">
            {counts.map((count) => (
              <article className="diaconia-counting-history-card" key={count.id}>
                <div>
                  <h2>{formatDate(count.date)}</h2>
                  <span>Responsavel: {count.created_by.display_name}</span>
                </div>
                <p>{count.items_count} itens contabilizados</p>
                <span>{count.locations_count} locais - registrada em {new Date(count.created_at).toLocaleString('pt-BR')}</span>
                <Link className="button button--secondary" to={`/diaconia/inventario/contagens/${count.id}`}>
                  <Eye size={16} aria-hidden="true" />
                  Ver contagem
                </Link>
              </article>
            ))}
          </div>
        </>
      )}
    </section>
  )
}

export default DiaconiaInventoryCountsPage
