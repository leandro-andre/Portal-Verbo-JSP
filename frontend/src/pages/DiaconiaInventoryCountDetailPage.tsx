import { Link, useParams } from 'react-router-dom'
import { GitCompareArrows, Pencil } from 'lucide-react'
import { useCan } from '../hooks/useAuth'
import { useInventoryCount } from '../hooks/useDiaconiaInventory'

function formatDate(value: string) {
  const [year, month, day] = value.split('-')
  if (!year || !month || !day) return value
  return `${day}/${month}/${year}`
}

function DiaconiaInventoryCountDetailPage() {
  const { id } = useParams()
  const countId = Number(id)
  const { data: count, isError, isLoading, refetch } = useInventoryCount(countId)
  const canManage = useCan('DIACONIA_INVENTORY_MANAGE')

  return (
    <section className="people-page">
      <nav className="breadcrumbs" aria-label="Breadcrumb">
        <Link to="/diaconia">Diaconia</Link>
        <span aria-hidden="true">/</span>
        <Link to="/diaconia/inventario">Inventario</Link>
        <span aria-hidden="true">/</span>
        <Link to="/diaconia/inventario/contagens">Contagens</Link>
        <span aria-hidden="true">/</span>
        <strong>Contagem</strong>
      </nav>

      {isLoading ? (
        <div className="state-panel"><h2>Carregando contagem...</h2></div>
      ) : isError || !count ? (
        <div className="state-panel state-panel--error">
          <h2>Nao foi possivel carregar a contagem.</h2>
          <button className="button button--secondary" type="button" onClick={() => void refetch()}>Tentar novamente</button>
        </div>
      ) : (
        <>
          <div className="page-heading">
            <div>
              <h1>Contagem de {formatDate(count.date)}</h1>
              <p className="page-heading__description">
                Responsavel: {count.created_by.display_name} - registrada em {new Date(count.created_at).toLocaleString('pt-BR')}
              </p>
            </div>
            <div className="diaconia-stock-actions">
              <Link className="button button--primary" to={`/diaconia/inventario/contagens/${count.id}/comparativo`}>
                <GitCompareArrows size={17} aria-hidden="true" />
                Comparar
              </Link>
              {canManage ? (
                <Link className="button button--secondary" to={`/diaconia/inventario/contagens/${count.id}/editar`}>
                  <Pencil size={17} aria-hidden="true" />
                  Editar
                </Link>
              ) : null}
              <Link className="button button--secondary" to="/diaconia/inventario/contagens">Voltar</Link>
            </div>
          </div>

          {count.notes ? (
            <div className="diaconia-stock-readonly">
              <span>Observacao</span>
              <strong>{count.notes}</strong>
            </div>
          ) : null}

          <div className="diaconia-counting-info-grid">
            <div className="diaconia-stock-readonly">
              <span>Responsavel</span>
              <strong>{count.created_by.display_name}</strong>
            </div>
            <div className="diaconia-stock-readonly">
              <span>Criado em</span>
              <strong>{new Date(count.created_at).toLocaleString('pt-BR')}</strong>
            </div>
            <div className="diaconia-stock-readonly">
              <span>Atualizado em</span>
              <strong>{new Date(count.updated_at).toLocaleString('pt-BR')}</strong>
            </div>
          </div>

          <div className="inventory-count-detail-list">
            {count.items.map((item) => (
              <article className="inventory-count-detail-card" key={item.item_id}>
                <div className="inventory-count-detail-card__heading">
                  <div>
                    <h2>{item.item_name}</h2>
                    <p>{item.category_name}</p>
                  </div>
                  <strong>Total: {item.total}</strong>
                </div>
                <div className="inventory-count-detail-card__locations">
                  {item.locations.map((location) => (
                    <div className="diaconia-counting-entry" key={location.location_id}>
                      <span>{location.location_name}</span>
                      <small>Quantidade</small>
                      <strong>{location.quantity}</strong>
                    </div>
                  ))}
                </div>
              </article>
            ))}
          </div>
        </>
      )}
    </section>
  )
}

export default DiaconiaInventoryCountDetailPage
