import { useMemo, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { Search } from 'lucide-react'
import { useInventoryCountComparison } from '../hooks/useDiaconiaInventory'
import type { InventoryComparisonStatus } from '../types/diaconiaInventory'

const statusLabels: Record<InventoryComparisonStatus, string> = {
  INCREASE: 'Aumento',
  DECREASE: 'Reducao',
  UNCHANGED: 'Sem alteracao',
  NEW: 'Novo na contagem',
  NOT_COUNTED: 'Nao contabilizado atualmente',
}

function formatDate(value: string) {
  const [year, month, day] = value.split('-')
  if (!year || !month || !day) return value
  return `${day}/${month}/${year}`
}

function formatVariation(value: number | null) {
  if (value === null) return '-'
  if (value > 0) return `+${value}`
  return String(value)
}

function formatPercent(value: number | null) {
  if (value === null) return '-'
  const formatted = value.toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
  return `${value > 0 ? '+' : ''}${formatted}%`
}

function statusClass(status: InventoryComparisonStatus) {
  return `inventory-comparison-status inventory-comparison-status--${status.toLowerCase().replace('_', '-')}`
}

function DiaconiaInventoryCountComparisonPage() {
  const { id } = useParams()
  const countId = Number(id)
  const { data: comparison, isError, isLoading, refetch } = useInventoryCountComparison(countId)
  const [search, setSearch] = useState('')

  const filteredItems = useMemo(() => {
    const normalizedSearch = search.trim().toLowerCase()
    if (!comparison || !normalizedSearch) return comparison?.items ?? []
    return comparison.items.filter((item) => item.item_name.toLowerCase().includes(normalizedSearch))
  }, [comparison, search])

  return (
    <section className="people-page">
      <nav className="breadcrumbs" aria-label="Breadcrumb">
        <Link to="/diaconia">Diaconia</Link>
        <span aria-hidden="true">/</span>
        <Link to="/diaconia/inventario">Inventario</Link>
        <span aria-hidden="true">/</span>
        <Link to="/diaconia/inventario/contagens">Contagens</Link>
        <span aria-hidden="true">/</span>
        <strong>Comparativo</strong>
      </nav>

      {isLoading ? (
        <div className="state-panel"><h2>Carregando comparativo...</h2></div>
      ) : isError || !comparison ? (
        <div className="state-panel state-panel--error">
          <h2>Nao foi possivel carregar o comparativo.</h2>
          <button className="button button--secondary" type="button" onClick={() => void refetch()}>Tentar novamente</button>
        </div>
      ) : (
        <>
          <div className="page-heading">
            <div>
              <h1>Comparativo de Inventario</h1>
              <p className="page-heading__description">
                Atual: {formatDate(comparison.current.date)}
                {comparison.previous ? ` - Anterior: ${formatDate(comparison.previous.date)}` : ''}
              </p>
            </div>
            <div className="diaconia-stock-actions">
              <Link className="button button--secondary" to={`/diaconia/inventario/contagens/${comparison.current.id}`}>Voltar</Link>
            </div>
          </div>

          {!comparison.previous ? (
            <div className="state-panel">
              <h2>Esta e a primeira contagem de inventario registrada.</h2>
              <p>Nao ha contagem anterior para comparacao.</p>
            </div>
          ) : (
            <>
              <p className="page-heading__description">Compare as quantidades encontradas entre as duas ultimas contagens.</p>

              <div className="inventory-comparison-summary">
                <div className="diaconia-stock-readonly">
                  <span>Itens com aumento</span>
                  <strong>{comparison.summary.increase}</strong>
                </div>
                <div className="diaconia-stock-readonly">
                  <span>Itens com reducao</span>
                  <strong>{comparison.summary.decrease}</strong>
                </div>
                <div className="diaconia-stock-readonly">
                  <span>Sem alteracao</span>
                  <strong>{comparison.summary.unchanged}</strong>
                </div>
                <div className="diaconia-stock-readonly">
                  <span>Novos na contagem</span>
                  <strong>{comparison.summary.new}</strong>
                </div>
                <div className="diaconia-stock-readonly">
                  <span>Nao contabilizados</span>
                  <strong>{comparison.summary.not_counted}</strong>
                </div>
              </div>

              <div className="field-group inventory-count-search">
                <label htmlFor="inventory-comparison-search">Buscar item</label>
                <div className="search-input">
                  <Search size={17} aria-hidden="true" />
                  <input
                    id="inventory-comparison-search"
                    type="search"
                    value={search}
                    onChange={(event) => setSearch(event.target.value)}
                    placeholder="Buscar item..."
                  />
                </div>
              </div>

              <div className="table-shell inventory-comparison-table">
                <table className="people-table">
                  <thead>
                    <tr>
                      <th>Item</th>
                      <th>Anterior</th>
                      <th>Atual</th>
                      <th>Variacao</th>
                      <th>Situacao</th>
                    </tr>
                  </thead>
                  <tbody>
                    {filteredItems.map((item) => (
                      <tr key={item.item_id}>
                        <td>
                          <strong>{item.item_name}</strong>
                          <span className="table-muted">{item.category_name}</span>
                          {item.locations.length ? (
                            <details className="inventory-comparison-locations">
                              <summary>Ver por local</summary>
                              <div className="inventory-comparison-location-list">
                                {item.locations.map((location) => (
                                  <div key={location.location_id}>
                                    <span>{location.location_name}</span>
                                    <strong>
                                      {location.previous_quantity ?? '-'} &gt; {location.current_quantity ?? '-'} ({formatVariation(location.variation)})
                                    </strong>
                                    <em>{statusLabels[location.status]}</em>
                                  </div>
                                ))}
                              </div>
                            </details>
                          ) : null}
                        </td>
                        <td>{item.previous_total ?? '-'}</td>
                        <td>{item.current_total ?? '-'}</td>
                        <td>{formatVariation(item.variation)} ({formatPercent(item.variation_percent)})</td>
                        <td><span className={statusClass(item.status)}>{statusLabels[item.status]}</span></td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              <div className="diaconia-counting-card-list inventory-comparison-cards">
                {filteredItems.map((item) => (
                  <article className="inventory-count-detail-card" key={item.item_id}>
                    <div className="inventory-count-detail-card__heading">
                      <div>
                        <h2>{item.item_name}</h2>
                        <p>{item.category_name}</p>
                      </div>
                      <span className={statusClass(item.status)}>{statusLabels[item.status]}</span>
                    </div>
                    <div className="inventory-comparison-card-metrics">
                      <div><span>Anterior</span><strong>{item.previous_total ?? '-'}</strong></div>
                      <div><span>Atual</span><strong>{item.current_total ?? '-'}</strong></div>
                      <div><span>Variacao</span><strong>{formatVariation(item.variation)} ({formatPercent(item.variation_percent)})</strong></div>
                    </div>
                    {item.locations.length ? (
                      <details className="inventory-comparison-locations">
                        <summary>Ver por local</summary>
                        <div className="inventory-comparison-location-list">
                          {item.locations.map((location) => (
                            <div key={location.location_id}>
                              <span>{location.location_name}</span>
                              <strong>
                                {location.previous_quantity ?? '-'} &gt; {location.current_quantity ?? '-'} ({formatVariation(location.variation)})
                              </strong>
                              <em>{statusLabels[location.status]}</em>
                            </div>
                          ))}
                        </div>
                      </details>
                    ) : null}
                  </article>
                ))}
              </div>
            </>
          )}
        </>
      )}
    </section>
  )
}

export default DiaconiaInventoryCountComparisonPage
