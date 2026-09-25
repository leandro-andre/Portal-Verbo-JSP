import { Archive, ArrowDown, ArrowRight, ClipboardCheck, Package, Plus, RefreshCw, TrendingDown, Users } from 'lucide-react'
import { Link } from 'react-router-dom'
import { useCan } from '../hooks/useAuth'
import { useDiaconiaDashboard } from '../hooks/useDiaconiaStock'
import type { DiaconiaDashboard } from '../types/diaconia'

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

function StockCard({ stock, canManageStock }: { stock: DiaconiaDashboard['stock']; canManageStock: boolean }) {
  const needsReplenishment = stock.low_stock_items > 0

  return (
    <article className="diaconia-dashboard-card">
      <div className="diaconia-dashboard-card__heading">
        <span className="diaconia-dashboard-card__icon" aria-hidden="true"><Package size={22} /></span>
        <div>
          <h2>Estoque</h2>
          <p>{needsReplenishment ? `${stock.low_stock_items} itens precisam de reposicao` : 'Nenhum item precisa de reposicao no momento.'}</p>
        </div>
      </div>
      <div className="diaconia-dashboard-metrics">
        <div><span>Ativos</span><strong>{stock.active_items}</strong></div>
        <div><span>Reposicao</span><strong>{stock.low_stock_items}</strong></div>
        <div><span>Sem minimo</span><strong>{stock.without_minimum_control}</strong></div>
      </div>
      <div className="diaconia-dashboard-actions">
        <Link className="button button--secondary" to="/diaconia/estoque">Ver estoque</Link>
        {canManageStock ? <Link className="button button--secondary" to="/diaconia/estoque/entrada">Nova entrada</Link> : null}
        {canManageStock ? <Link className="button button--secondary" to="/diaconia/estoque/saida">Nova saida</Link> : null}
      </div>
    </article>
  )
}

function AttendanceCard({ attendance, canManageCounting }: { attendance: DiaconiaDashboard['attendance']; canManageCounting: boolean }) {
  return (
    <article className="diaconia-dashboard-card">
      <div className="diaconia-dashboard-card__heading">
        <span className="diaconia-dashboard-card__icon" aria-hidden="true"><Users size={22} /></span>
        <div>
          <h2>Publico</h2>
          {attendance.latest ? (
            <p>{attendance.latest.total_people} pessoas na ultima contagem</p>
          ) : (
            <p>Nenhuma contagem de publico registrada.</p>
          )}
        </div>
      </div>
      {attendance.latest ? (
        <>
          <div className="diaconia-dashboard-highlight">
            <strong>{attendance.latest.total_people}</strong>
            <span>{attendance.latest.shift_label} - {formatDate(attendance.latest.date)}</span>
          </div>
          <p className="diaconia-dashboard-card__note">
            {attendance.comparison
              ? `${formatVariation(attendance.comparison.variation)} (${formatPercent(attendance.comparison.variation_percent)}) em relacao a contagem anterior`
              : 'Ainda nao ha contagem anterior para comparacao.'}
          </p>
        </>
      ) : null}
      <div className="diaconia-dashboard-actions">
        <Link className="button button--secondary" to="/diaconia/contagens">Ver contagens</Link>
        {canManageCounting ? <Link className="button button--secondary" to="/diaconia/contagens/nova">Realizar contagem</Link> : null}
      </div>
    </article>
  )
}

function InventoryCard({ inventory, canManageInventory }: { inventory: DiaconiaDashboard['inventory']; canManageInventory: boolean }) {
  return (
    <article className="diaconia-dashboard-card">
      <div className="diaconia-dashboard-card__heading">
        <span className="diaconia-dashboard-card__icon" aria-hidden="true"><Archive size={22} /></span>
        <div>
          <h2>Inventario</h2>
          {inventory.latest ? (
            <p>Ultima contagem: {formatDate(inventory.latest.date)}</p>
          ) : (
            <p>Nenhuma contagem de inventario registrada.</p>
          )}
        </div>
      </div>
      {inventory.latest && inventory.summary ? (
        inventory.previous ? (
          <div className="diaconia-dashboard-metrics">
            <div><span>Reducao</span><strong>{inventory.summary.decrease}</strong></div>
            <div><span>Aumento</span><strong>{inventory.summary.increase}</strong></div>
            <div><span>Sem alteracao</span><strong>{inventory.summary.unchanged}</strong></div>
            <div><span>Novos</span><strong>{inventory.summary.new}</strong></div>
            <div><span>Nao contabilizados</span><strong>{inventory.summary.not_counted}</strong></div>
          </div>
        ) : (
          <p className="diaconia-dashboard-card__note">Primeira contagem registrada. Ainda nao ha comparativo disponivel.</p>
        )
      ) : null}
      <div className="diaconia-dashboard-actions">
        {inventory.latest && inventory.previous ? (
          <Link className="button button--secondary" to={`/diaconia/inventario/contagens/${inventory.latest.id}/comparativo`}>Ver comparativo</Link>
        ) : inventory.latest ? (
          <Link className="button button--secondary" to={`/diaconia/inventario/contagens/${inventory.latest.id}`}>Ver contagem</Link>
        ) : null}
        <Link className="button button--secondary" to="/diaconia/inventario/contagens">Ver historico</Link>
        {canManageInventory ? <Link className="button button--secondary" to="/diaconia/inventario/contagens/nova">Realizar contagem</Link> : null}
      </div>
    </article>
  )
}

function DiaconiaPage() {
  const { data: dashboard, isError, isLoading, refetch } = useDiaconiaDashboard()
  const canManageStock = useCan('DIACONIA_STOCK_MANAGE')
  const canManageCounting = useCan('DIACONIA_COUNTING_MANAGE')
  const canManageInventory = useCan('DIACONIA_INVENTORY_MANAGE')

  return (
    <section className="diaconia-page">
      <div className="page-heading">
        <div>
          <h1>Diaconia</h1>
          <p className="page-heading__description">Visao operacional de estoque, publico e inventario.</p>
        </div>
      </div>

      {isLoading ? (
        <div className="state-panel"><h2>Carregando Central da Diaconia...</h2></div>
      ) : isError || !dashboard ? (
        <div className="state-panel state-panel--error">
          <h2>Nao foi possivel carregar a Central da Diaconia.</h2>
          <button className="button button--secondary" type="button" onClick={() => void refetch()}>
            <RefreshCw size={17} aria-hidden="true" />
            Tentar novamente
          </button>
        </div>
      ) : (
        <>
          <div className="diaconia-dashboard-grid">
            <StockCard stock={dashboard.stock} canManageStock={canManageStock} />
            <AttendanceCard attendance={dashboard.attendance} canManageCounting={canManageCounting} />
            <InventoryCard inventory={dashboard.inventory} canManageInventory={canManageInventory} />
          </div>

          <section className="diaconia-dashboard-section">
            <div className="diaconia-dashboard-section__heading">
              <h2>Atencoes</h2>
              <p>Prioridades operacionais para acompanhamento da Diaconia.</p>
            </div>
            <div className="diaconia-dashboard-attention-grid">
              <article className="diaconia-dashboard-panel">
                <div className="diaconia-dashboard-panel__heading">
                  <Package size={20} aria-hidden="true" />
                  <h3>Itens para reposicao</h3>
                </div>
                {dashboard.stock.replenishment_items.length ? (
                  <div className="diaconia-dashboard-list">
                    {dashboard.stock.replenishment_items.map((item) => (
                      <div className="diaconia-dashboard-list__item" key={item.id}>
                        <div>
                          <strong>{item.name}</strong>
                          <span>{item.category.name} - {item.unit_label}</span>
                        </div>
                        <p>{item.current_stock} atual / minimo {item.minimum_stock}</p>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="diaconia-dashboard-empty">Nenhum item precisa de reposicao no momento.</p>
                )}
                <Link className="button button--secondary" to="/diaconia/estoque">
                  Ver estoque
                  <ArrowRight size={16} aria-hidden="true" />
                </Link>
              </article>

              <article className="diaconia-dashboard-panel">
                <div className="diaconia-dashboard-panel__heading">
                  <TrendingDown size={20} aria-hidden="true" />
                  <h3>Reducoes no inventario</h3>
                </div>
                {dashboard.inventory.has_data && dashboard.inventory.previous && dashboard.inventory.reductions.length ? (
                  <div className="diaconia-dashboard-list">
                    {dashboard.inventory.reductions.map((item) => (
                      <div className="diaconia-dashboard-list__item" key={item.item_id}>
                        <div>
                          <strong>{item.item_name}</strong>
                          <span>{item.category_name}</span>
                        </div>
                        <p>{formatVariation(item.variation)} ({formatPercent(item.variation_percent)})</p>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="diaconia-dashboard-empty">
                    {dashboard.inventory.has_data && !dashboard.inventory.previous
                      ? 'Primeira contagem registrada. Ainda nao ha comparativo.'
                      : 'Nenhuma reducao de inventario identificada no ultimo comparativo.'}
                  </p>
                )}
                {dashboard.inventory.latest && dashboard.inventory.previous ? (
                  <Link className="button button--secondary" to={`/diaconia/inventario/contagens/${dashboard.inventory.latest.id}/comparativo`}>
                    Ver comparativo
                    <ArrowRight size={16} aria-hidden="true" />
                  </Link>
                ) : (
                  <Link className="button button--secondary" to="/diaconia/inventario/contagens">
                    Ver historico
                    <ArrowRight size={16} aria-hidden="true" />
                  </Link>
                )}
              </article>
            </div>
          </section>

          <section className="diaconia-dashboard-section">
            <div className="diaconia-dashboard-section__heading">
              <h2>Ultima contagem de publico</h2>
              <p>Distribuicao por ambiente no snapshot mais recente.</p>
            </div>
            <article className="diaconia-dashboard-panel">
              {dashboard.attendance.latest ? (
                <>
                  <div className="diaconia-dashboard-public-heading">
                    <div>
                      <strong>{dashboard.attendance.latest.total_people} pessoas</strong>
                      <span>{dashboard.attendance.latest.shift_label} - {formatDate(dashboard.attendance.latest.date)}</span>
                    </div>
                    <p>
                      {dashboard.attendance.comparison
                        ? `${formatVariation(dashboard.attendance.comparison.variation)} (${formatPercent(dashboard.attendance.comparison.variation_percent)})`
                        : 'Sem comparativo anterior'}
                    </p>
                  </div>
                  <div className="diaconia-dashboard-bars">
                    {dashboard.attendance.distribution.map((entry) => {
                      const percent = dashboard.attendance.latest?.total_people
                        ? Math.round((entry.quantity / dashboard.attendance.latest.total_people) * 100)
                        : 0
                      return (
                        <div className="diaconia-dashboard-bar" key={entry.environment_id}>
                          <div>
                            <span>{entry.environment_name}</span>
                            <strong>{entry.quantity}</strong>
                          </div>
                          <div className="diaconia-dashboard-bar__track">
                            <span style={{ width: `${percent}%` }} />
                          </div>
                        </div>
                      )
                    })}
                  </div>
                </>
              ) : (
                <p className="diaconia-dashboard-empty">Nenhuma contagem de publico registrada.</p>
              )}
              <div className="diaconia-dashboard-actions">
                <Link className="button button--secondary" to="/diaconia/contagens">Ver contagens</Link>
                {canManageCounting ? <Link className="button button--secondary" to="/diaconia/contagens/nova">Realizar contagem</Link> : null}
              </div>
            </article>
          </section>

          <section className="diaconia-dashboard-section">
            <div className="diaconia-dashboard-section__heading">
              <h2>Atalhos operacionais</h2>
            </div>
            <div className="diaconia-dashboard-shortcuts">
              {canManageStock ? <Link className="button button--primary" to="/diaconia/estoque/entrada"><Plus size={17} aria-hidden="true" />Nova entrada</Link> : null}
              {canManageStock ? <Link className="button button--secondary" to="/diaconia/estoque/saida"><ArrowDown size={17} aria-hidden="true" />Nova saida</Link> : null}
              {canManageCounting ? <Link className="button button--secondary" to="/diaconia/contagens/nova"><ClipboardCheck size={17} aria-hidden="true" />Contagem de publico</Link> : null}
              {canManageInventory ? <Link className="button button--secondary" to="/diaconia/inventario/contagens/nova"><Archive size={17} aria-hidden="true" />Contagem de inventario</Link> : null}
            </div>
          </section>
        </>
      )}
    </section>
  )
}

export default DiaconiaPage
