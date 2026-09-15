import { Boxes, ClipboardList, FolderTree, MapPinned, PackageSearch } from 'lucide-react'
import { Link } from 'react-router-dom'

const inventoryAreas = [
  {
    title: 'Contagens',
    description: 'Registre a fotografia fisica dos bens encontrados por local.',
    action: 'Realizar contagem',
    to: '/diaconia/inventario/contagens',
    icon: ClipboardList,
  },
  {
    title: 'Itens',
    description: 'Cadastre os tipos de bens controlados no inventario.',
    action: 'Gerenciar itens',
    to: '/diaconia/inventario/itens',
    icon: PackageSearch,
  },
  {
    title: 'Categorias',
    description: 'Organize os tipos de bens do inventario.',
    action: 'Gerenciar categorias',
    to: '/diaconia/inventario/categorias',
    icon: FolderTree,
  },
  {
    title: 'Locais',
    description: 'Defina onde os bens da igreja podem estar alocados.',
    action: 'Gerenciar locais',
    to: '/diaconia/inventario/locais',
    icon: MapPinned,
  },
]

function DiaconiaInventoryPage() {
  return (
    <section className="people-page">
      <nav className="breadcrumbs" aria-label="Breadcrumb">
        <Link to="/diaconia">Diaconia</Link>
        <span aria-hidden="true">/</span>
        <strong>Inventario</strong>
      </nav>

      <div className="page-heading">
        <div>
          <h1>Inventario</h1>
          <p className="page-heading__description">Gerencie os bens e sua distribuicao pelos locais da igreja.</p>
        </div>
      </div>

      <div className="diaconia-counting-hero">
        <div className="diaconia-counting-hero__icon" aria-hidden="true">
          <Boxes size={28} />
        </div>
        <div>
          <h2>Inventario de bens</h2>
          <p>Registre periodicamente a quantidade fisica encontrada de cada bem nos locais da igreja.</p>
        </div>
      </div>

      <div className="diaconia-area-grid">
        {inventoryAreas.map((area) => {
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
              <Link className="button button--secondary" to={area.to}>{area.action}</Link>
            </article>
          )
        })}
      </div>
    </section>
  )
}

export default DiaconiaInventoryPage
