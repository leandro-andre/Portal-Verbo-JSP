export type StockCategory = {
  id: number
  name: string
  description: string
  is_active: boolean
  created_at: string
  updated_at: string
}

export type StockUnit = {
  value: string
  label: string
}

export type StockItem = {
  id: number
  name: string
  category: Pick<StockCategory, 'id' | 'name' | 'is_active'>
  unit: string
  unit_label: string
  current_stock: number
  minimum_stock: number
  notes: string
  is_active: boolean
  created_at: string
  updated_at: string
}

export type CreateStockCategoryInput = {
  name: string
  description: string
}

export type UpdateStockCategoryInput = CreateStockCategoryInput

export type CreateStockItemInput = {
  name: string
  category_id: number
  unit: string
  minimum_stock: number
  notes: string
}

export type UpdateStockItemInput = CreateStockItemInput

export type DiaconiaValidationErrors = Partial<Record<string, string[]>>

export type StockMovementType = 'ENTRADA' | 'SAIDA'

export type StockMovement = {
  id: number
  item: Pick<StockItem, 'id' | 'name' | 'unit' | 'unit_label' | 'is_active'>
  movement_type: StockMovementType
  movement_type_label: string
  quantity: number
  notes: string
  created_by: {
    id: number
    display_name: string
  }
  created_at: string
}

export type CreateStockMovementInput = {
  item_id: number
  movement_type: StockMovementType
  quantity: number
  notes: string
}
