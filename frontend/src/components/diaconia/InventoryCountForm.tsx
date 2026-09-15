import { useMemo, useState } from 'react'

type QuantityState = Record<string, string>

export type InventoryCountFormItem = {
  id: number
  name: string
  category: {
    id: number
    name: string
  }
}

export type InventoryCountFormLocation = {
  id: number
  name: string
}

function inventoryCountMatrixKey(itemId: number, locationId: number) {
  return `${itemId}:${locationId}`
}

function sanitizeQuantity(value: string) {
  return value.replace(/[^\d]/g, '') || '0'
}

function quantityValue(quantities: QuantityState, itemId: number, locationId: number) {
  const value = Number.parseInt(quantities[inventoryCountMatrixKey(itemId, locationId)] || '0', 10)
  return Number.isFinite(value) && value > 0 ? value : 0
}

type InventoryCountFormProps = {
  items: InventoryCountFormItem[]
  locations: InventoryCountFormLocation[]
  itemLocationIds?: Record<number, number[]>
  quantities: QuantityState
  onQuantitiesChange: (quantities: QuantityState) => void
}

function InventoryCountForm({ items, locations, itemLocationIds, quantities, onQuantitiesChange }: InventoryCountFormProps) {
  const [search, setSearch] = useState('')
  const locationsById = useMemo(() => new Map(locations.map((location) => [location.id, location])), [locations])

  const itemsByCategory = useMemo(() => {
    const normalizedSearch = search.trim().toLowerCase()
    const groups = new Map<string, { categoryName: string; items: InventoryCountFormItem[] }>()
    items.forEach((item) => {
      if (normalizedSearch && !item.name.toLowerCase().includes(normalizedSearch)) return
      const key = `${item.category.id}:${item.category.name}`
      const group = groups.get(key) ?? { categoryName: item.category.name, items: [] }
      group.items.push(item)
      groups.set(key, group)
    })
    return Array.from(groups.values())
  }, [items, search])

  const itemLocations = (itemId: number) => {
    const locationIds = itemLocationIds?.[itemId]
    if (!locationIds) return locations
    return locationIds
      .map((locationId) => locationsById.get(locationId))
      .filter((location): location is InventoryCountFormLocation => Boolean(location))
  }

  const hasLocationForItem = (itemId: number, locationId: number) =>
    itemLocations(itemId).some((location) => location.id === locationId)

  const setQuantity = (itemId: number, locationId: number, value: string) => {
    onQuantitiesChange({
      ...quantities,
      [inventoryCountMatrixKey(itemId, locationId)]: sanitizeQuantity(value),
    })
  }

  const itemTotal = (item: InventoryCountFormItem) =>
    itemLocations(item.id).reduce((sum, location) => sum + quantityValue(quantities, item.id, location.id), 0)

  return (
    <div className="inventory-count-form">
      <div className="field-group inventory-count-search">
        <label htmlFor="inventory-count-search">Buscar item</label>
        <input
          id="inventory-count-search"
          type="search"
          value={search}
          onChange={(event) => setSearch(event.target.value)}
          placeholder="Buscar item..."
        />
      </div>

      {itemsByCategory.length === 0 ? (
        <div className="state-panel state-panel--compact">
          <h2>Nenhum item encontrado.</h2>
          <p>A busca apenas altera o que aparece na tela; os valores ja preenchidos permanecem na contagem.</p>
        </div>
      ) : null}

      <div className="inventory-count-matrix" aria-label="Matriz de contagem de inventario">
        {itemsByCategory.map((group) => (
          <section className="inventory-count-category" key={group.categoryName}>
            <h2>{group.categoryName}</h2>
            <div className="table-shell inventory-count-table-shell">
              <table className="people-table inventory-count-table">
                <thead>
                  <tr>
                    <th>Item</th>
                    {locations.map((location) => (
                      <th key={location.id}>{location.name}</th>
                    ))}
                    <th>Total</th>
                  </tr>
                </thead>
                <tbody>
                  {group.items.map((item) => (
                    <tr key={item.id}>
                      <td>
                        <strong>{item.name}</strong>
                      </td>
                      {locations.map((location) => (
                        <td key={location.id}>
                          {hasLocationForItem(item.id, location.id) ? (
                            <input
                              className="table-input inventory-count-cell-input"
                              type="number"
                              inputMode="numeric"
                              min="0"
                              step="1"
                              value={quantities[inventoryCountMatrixKey(item.id, location.id)] ?? '0'}
                              onChange={(event) => setQuantity(item.id, location.id, event.target.value)}
                              aria-label={`${item.name} em ${location.name}`}
                            />
                          ) : (
                            <span className="table-muted">-</span>
                          )}
                        </td>
                      ))}
                      <td>
                        <strong>{itemTotal(item)}</strong>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>
        ))}
      </div>

      <div className="inventory-count-mobile-list">
        {itemsByCategory.map((group) => (
          <section className="inventory-count-category" key={group.categoryName}>
            <h2>{group.categoryName}</h2>
            <div className="diaconia-counting-card-list">
              {group.items.map((item) => (
                <article className="inventory-count-mobile-card" key={item.id}>
                  <div className="inventory-count-mobile-card__heading">
                    <div>
                      <h3>{item.name}</h3>
                      <p>{item.category.name}</p>
                    </div>
                    <strong>Total: {itemTotal(item)}</strong>
                  </div>
                  <div className="inventory-count-mobile-card__locations">
                    {itemLocations(item.id).map((location) => (
                      <label className="diaconia-counting-entry" key={location.id} htmlFor={`mobile-${item.id}-${location.id}`}>
                        <span>{location.name}</span>
                        <small>Quantidade</small>
                        <input
                          id={`mobile-${item.id}-${location.id}`}
                          type="number"
                          inputMode="numeric"
                          min="0"
                          step="1"
                          value={quantities[inventoryCountMatrixKey(item.id, location.id)] ?? '0'}
                          onChange={(event) => setQuantity(item.id, location.id, event.target.value)}
                        />
                      </label>
                    ))}
                  </div>
                </article>
              ))}
            </div>
          </section>
        ))}
      </div>
    </div>
  )
}

export default InventoryCountForm
