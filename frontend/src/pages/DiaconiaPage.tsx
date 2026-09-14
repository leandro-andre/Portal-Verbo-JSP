import { Archive, ClipboardCheck, Package } from 'lucide-react'

const areas = [
  {
    title: 'Estoque',
    description: 'Controle de materiais utilizados pela igreja, entradas, retiradas e niveis de estoque.',
    action: 'Acessar estoque',
    icon: Package,
  },
  {
    title: 'Contagens',
    description: 'Registro de publico por ambiente, data e turno.',
    action: 'Realizar contagem',
    icon: ClipboardCheck,
  },
  {
    title: 'Inventario',
    description: 'Controle dos bens e quantidades administrados pela Diaconia.',
    action: 'Acessar inventario',
    icon: Archive,
  },
]

function DiaconiaPage() {
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
              </div>
              <button className="button button--secondary" type="button" disabled>
                {area.action}
                <span className="status-badge diaconia-area-card__badge">Em breve</span>
              </button>
            </article>
          )
        })}
      </div>
    </section>
  )
}

export default DiaconiaPage
