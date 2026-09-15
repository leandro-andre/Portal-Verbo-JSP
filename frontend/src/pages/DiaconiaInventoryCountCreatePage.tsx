import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { MapPinned, PackageSearch, Save } from 'lucide-react'
import { DiaconiaApiValidationError, DiaconiaBusinessError } from '../api/diaconia'
import InventoryCountForm from '../components/diaconia/InventoryCountForm'
import { useCreateInventoryCount, useInventoryItems, useInventoryLocations } from '../hooks/useDiaconiaInventory'

function todayInputValue() {
  const date = new Date()
  const timezoneOffset = date.getTimezoneOffset() * 60000
  return new Date(date.getTime() - timezoneOffset).toISOString().slice(0, 10)
}

function formatDate(value: string) {
  const [year, month, day] = value.split('-')
  if (!year || !month || !day) return value
  return `${day}/${month}/${year}`
}

function quantityKey(itemId: number, locationId: number) {
  return `${itemId}:${locationId}`
}

function DiaconiaInventoryCountCreatePage() {
  const navigate = useNavigate()
  const { data: items = [], isError: itemsError, isLoading: itemsLoading, refetch: refetchItems } = useInventoryItems({ status: 'ACTIVE' })
  const { data: locations = [], isError: locationsError, isLoading: locationsLoading, refetch: refetchLocations } = useInventoryLocations({ status: 'ACTIVE' })
  const createInventoryCount = useCreateInventoryCount()
  const [date, setDate] = useState(todayInputValue)
  const [notes, setNotes] = useState('')
  const [quantities, setQuantities] = useState<Record<string, string>>({})
  const [error, setError] = useState<string | null>(null)

  const isLoading = itemsLoading || locationsLoading
  const isError = itemsError || locationsError
  const isSubmitting = createInventoryCount.isPending

  const handleSubmit = async () => {
    setError(null)
    if (!items.length || !locations.length) return
    if (!window.confirm(`Finalizar contagem de inventario de ${formatDate(date)}?`)) return

    try {
      const created = await createInventoryCount.mutateAsync({
        date,
        notes,
        entries: items.flatMap((item) =>
          locations.map((location) => ({
            item_id: item.id,
            location_id: location.id,
            quantity: Number.parseInt(quantities[quantityKey(item.id, location.id)] || '0', 10),
          })),
        ),
      })
      navigate(`/diaconia/inventario/contagens/${created.id}`)
    } catch (submitError) {
      if (submitError instanceof DiaconiaApiValidationError) {
        const firstMessage = Object.values(submitError.fieldErrors).flat()[0]
        setError(firstMessage ?? 'Confira os dados da contagem.')
        return
      }
      if (submitError instanceof DiaconiaBusinessError) {
        setError(submitError.message)
        return
      }
      setError('Nao foi possivel registrar a contagem.')
    }
  }

  return (
    <section className="people-page">
      <nav className="breadcrumbs" aria-label="Breadcrumb">
        <Link to="/diaconia">Diaconia</Link>
        <span aria-hidden="true">/</span>
        <Link to="/diaconia/inventario">Inventario</Link>
        <span aria-hidden="true">/</span>
        <Link to="/diaconia/inventario/contagens">Contagens</Link>
        <span aria-hidden="true">/</span>
        <strong>Nova contagem</strong>
      </nav>

      <div className="page-heading">
        <div>
          <h1>Nova contagem de inventario</h1>
          <p className="page-heading__description">Informe a quantidade fisica encontrada de cada item em cada local ativo.</p>
        </div>
      </div>

      {error ? <div className="form-alert form-alert--error" role="alert">{error}</div> : null}

      {isLoading ? (
        <div className="state-panel"><h2>Carregando itens e locais...</h2></div>
      ) : isError ? (
        <div className="state-panel state-panel--error">
          <h2>Nao foi possivel carregar itens e locais.</h2>
          <button
            className="button button--secondary"
            type="button"
            onClick={() => {
              void refetchItems()
              void refetchLocations()
            }}
          >
            Tentar novamente
          </button>
        </div>
      ) : items.length === 0 ? (
        <div className="state-panel">
          <h2>Nenhum item ativo disponivel para contagem.</h2>
          <p>Cadastre ou reative itens antes de iniciar a contagem.</p>
          <Link className="button button--primary" to="/diaconia/inventario/itens">
            <PackageSearch size={17} aria-hidden="true" />
            Gerenciar itens
          </Link>
        </div>
      ) : locations.length === 0 ? (
        <div className="state-panel">
          <h2>Nenhum local ativo disponivel para contagem.</h2>
          <p>Cadastre ou reative locais antes de iniciar a contagem.</p>
          <Link className="button button--primary" to="/diaconia/inventario/locais">
            <MapPinned size={17} aria-hidden="true" />
            Gerenciar locais
          </Link>
        </div>
      ) : (
        <>
          <div className="diaconia-counting-form">
            <div className="form-grid">
              <div className="field-group">
                <label htmlFor="inventory-count-date">Data da contagem</label>
                <input id="inventory-count-date" type="date" value={date} onChange={(event) => setDate(event.target.value)} required />
              </div>
              <div className="field-group field-group--wide">
                <label htmlFor="inventory-count-notes">Observacao</label>
                <textarea
                  id="inventory-count-notes"
                  value={notes}
                  onChange={(event) => setNotes(event.target.value)}
                  rows={3}
                  placeholder="Contagem geral realizada pela Diaconia."
                />
              </div>
            </div>
          </div>

          <InventoryCountForm items={items} locations={locations} quantities={quantities} onQuantitiesChange={setQuantities} />

          <div className="form-actions">
            <button className="button button--primary" type="button" disabled={isSubmitting || !date} onClick={() => void handleSubmit()}>
              <Save size={17} aria-hidden="true" />
              Finalizar contagem
            </button>
            <Link className="button button--secondary" to="/diaconia/inventario/contagens">Cancelar</Link>
          </div>
        </>
      )}
    </section>
  )
}

export default DiaconiaInventoryCountCreatePage
