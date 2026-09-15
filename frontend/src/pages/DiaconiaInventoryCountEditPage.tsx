import { useMemo, useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { Save } from 'lucide-react'
import { DiaconiaApiValidationError, DiaconiaBusinessError } from '../api/diaconia'
import InventoryCountForm from '../components/diaconia/InventoryCountForm'
import { useInventoryCount, useUpdateInventoryCount } from '../hooks/useDiaconiaInventory'
import type { InventoryCount } from '../types/diaconiaInventory'

function formatDate(value: string) {
  const [year, month, day] = value.split('-')
  if (!year || !month || !day) return value
  return `${day}/${month}/${year}`
}

function matrixKey(itemId: number, locationId: number) {
  return `${itemId}:${locationId}`
}

function initialQuantities(count: InventoryCount) {
  const quantities: Record<string, string> = {}
  count.items.forEach((item) => {
    item.locations.forEach((location) => {
      quantities[matrixKey(item.item_id, location.location_id)] = String(location.quantity)
    })
  })
  return quantities
}

function InventoryCountEditForm({ count }: { count: InventoryCount }) {
  const navigate = useNavigate()
  const updateInventoryCount = useUpdateInventoryCount(count.id)
  const [date, setDate] = useState(count.date)
  const [notes, setNotes] = useState(count.notes)
  const [quantities, setQuantities] = useState<Record<string, string>>(() => initialQuantities(count))
  const [error, setError] = useState<string | null>(null)

  const formData = useMemo(() => {
    const locationsById = new Map<number, { id: number; name: string }>()
    const itemLocationIds: Record<number, number[]> = {}
    const items = count.items.map((item) => {
      itemLocationIds[item.item_id] = item.locations.map((location) => {
        locationsById.set(location.location_id, { id: location.location_id, name: location.location_name })
        return location.location_id
      })
      return {
        id: item.item_id,
        name: item.item_name,
        category: { id: item.category_id, name: item.category_name },
      }
    })
    return { items, locations: Array.from(locationsById.values()), itemLocationIds }
  }, [count])

  const handleSubmit = async () => {
    setError(null)
    if (!window.confirm(`Salvar correcoes da contagem de ${formatDate(count.date)}?`)) return

    try {
      const updated = await updateInventoryCount.mutateAsync({
        date,
        notes,
        entries: count.items.flatMap((item) =>
          item.locations.map((location) => ({
            item_id: item.item_id,
            location_id: location.location_id,
            quantity: Number.parseInt(quantities[matrixKey(item.item_id, location.location_id)] || '0', 10),
          })),
        ),
      })
      navigate(`/diaconia/inventario/contagens/${updated.id}`)
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
      setError('Nao foi possivel salvar as correcoes.')
    }
  }

  return (
    <>
      <div className="page-heading">
        <div>
          <h1>Corrigir contagem de inventario</h1>
          <p className="page-heading__description">Ajuste data, observacao e quantidades mantendo a composicao historica original.</p>
        </div>
      </div>

      {error ? <div className="form-alert form-alert--error" role="alert">{error}</div> : null}

      <div className="diaconia-counting-form">
        <div className="form-grid">
          <div className="field-group">
            <label htmlFor="inventory-count-edit-date">Data da contagem</label>
            <input id="inventory-count-edit-date" type="date" value={date} onChange={(event) => setDate(event.target.value)} required />
          </div>
          <div className="field-group field-group--wide">
            <label htmlFor="inventory-count-edit-notes">Observacao</label>
            <textarea
              id="inventory-count-edit-notes"
              value={notes}
              onChange={(event) => setNotes(event.target.value)}
              rows={3}
            />
          </div>
        </div>
      </div>

      <InventoryCountForm
        items={formData.items}
        locations={formData.locations}
        itemLocationIds={formData.itemLocationIds}
        quantities={quantities}
        onQuantitiesChange={setQuantities}
      />

      <div className="form-actions">
        <button className="button button--primary" type="button" disabled={updateInventoryCount.isPending || !date} onClick={() => void handleSubmit()}>
          <Save size={17} aria-hidden="true" />
          Salvar correcoes
        </button>
        <Link className="button button--secondary" to={`/diaconia/inventario/contagens/${count.id}`}>Cancelar</Link>
      </div>
    </>
  )
}

function DiaconiaInventoryCountEditPage() {
  const { id } = useParams()
  const countId = Number(id)
  const { data: count, isError, isLoading, refetch } = useInventoryCount(countId)

  return (
    <section className="people-page">
      <nav className="breadcrumbs" aria-label="Breadcrumb">
        <Link to="/diaconia">Diaconia</Link>
        <span aria-hidden="true">/</span>
        <Link to="/diaconia/inventario">Inventario</Link>
        <span aria-hidden="true">/</span>
        <Link to="/diaconia/inventario/contagens">Contagens</Link>
        <span aria-hidden="true">/</span>
        <strong>Editar</strong>
      </nav>

      {isLoading ? (
        <div className="state-panel"><h2>Carregando contagem...</h2></div>
      ) : isError || !count ? (
        <div className="state-panel state-panel--error">
          <h2>Nao foi possivel carregar a contagem.</h2>
          <button className="button button--secondary" type="button" onClick={() => void refetch()}>Tentar novamente</button>
        </div>
      ) : (
        <InventoryCountEditForm key={count.id} count={count} />
      )}
    </section>
  )
}

export default DiaconiaInventoryCountEditPage
