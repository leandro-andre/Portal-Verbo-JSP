import { Archive, ClipboardCheck, Package } from 'lucide-react'
import { Link } from 'react-router-dom'
import { useStockSummary } from '../hooks/useDiaconiaStock'

const areas = [
  {
    title: 'Estoque',
    description: 'Controle de materiais utilizados pela igreja, entradas, retiradas e niveis de estoque.',
    action: 'Acessar estoque',
    to: '/diaconia/estoque',
    icon: Package,
  },
  {
    title: 'Contagens',
    description: 'Registro de publico por ambiente, data e turno.',
    action: 'Acessar contagens',
    to: '/diaconia/contagens',
    icon: ClipboardCheck,
  },
  {
    title: 'Inventario',
    description: 'Controle dos bens e quantidades administrados pela Diaconia.',
    action: 'Acessar inventario',
    to: '/diaconia/inventario',
    icon: Archive,
  },
]

function DiaconiaPage() {
  const { data: stockSummary } = useStockSummary()

  return (
    <section className="diaconia-page">
      <div className="page-heading">
        <div>
          <h1>Diaconia</h1>
          <p className="page-heading__description">Gestao operacional do departamento</p>
        </div>
      </div>

      <div className="diaconia-overview">
        <div>
          <span className="status-badge status-badge--active">Visao Geral</span>
          <h2>Estrutura inicial do modulo</h2>
          <p>
            Esta area centraliza os fluxos operacionais da Diaconia e esta preparada para receber
            estoque, contagens e inventario nas proximas etapas.
          </p>
        </div>
      </div>

      <div className="diaconia-area-grid">
        {areas.map((area) => {
          const Icon = area.icon
          return (
            <article className="diaconia-area-card" key={area.title}>
              <div className="diaconia-area-card__icon" aria-hidden="true">
                <Icon size={22} />
              </div>
              <div className="diaconia-area-card__content">
                <h2>{area.title}</h2>
                <p>{area.description}</p>
                {area.title === 'Estoque' && stockSummary ? (
                  <div className="diaconia-area-card__summary">
                    <span>{stockSummary.active_items} itens ativos</span>
                    <span>
                      {stockSummary.low_stock_items > 0
                        ? `${stockSummary.low_stock_items} precisam de reposicao`
                        : 'Estoque dentro dos niveis minimos'}
                    </span>
                  </div>
                ) : null}
              </div>
              <Link className="button button--secondary" to={area.to}>
                {area.action}
              </Link>
            </article>
          )
        })}
      </div>
    </section>
  )
}

export default DiaconiaPage
