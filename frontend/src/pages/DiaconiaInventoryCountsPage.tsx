import { ClipboardList, Plus } from 'lucide-react'
import { Link } from 'react-router-dom'
import { useCan } from '../hooks/useAuth'

function DiaconiaInventoryCountsPage() {
  const canManage = useCan('DIACONIA_INVENTORY_MANAGE')

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
          <h1>Contagem de Inventario</h1>
          <p className="page-heading__description">Registre a quantidade fisica encontrada de cada bem nos locais da igreja.</p>
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

      <div className="diaconia-counting-hero">
        <div className="diaconia-counting-hero__icon" aria-hidden="true">
          <ClipboardList size={28} />
        </div>
        <div>
          <h2>Inventario periodico</h2>
          <p>As contagens registram uma fotografia fisica por data. Historico e comparativos serao evoluidos na proxima etapa.</p>
        </div>
      </div>
    </section>
  )
}

export default DiaconiaInventoryCountsPage
