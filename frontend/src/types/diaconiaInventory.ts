export type InventoryCategory = {
  id: number
  name: string
  description: string
  is_active: boolean
  created_at: string
  updated_at: string
}

export type InventoryLocation = {
  id: number
  name: string
  description: string
  is_active: boolean
  created_at: string
  updated_at: string
}

export type InventoryItem = {
  id: number
  name: string
  description: string
  category: Pick<InventoryCategory, 'id' | 'name' | 'is_active'>
  is_active: boolean
  created_at: string
  updated_at: string
}

export type InventoryFilters = {
  search?: string
  status?: 'ACTIVE' | 'INACTIVE' | 'ALL'
}

export type InventoryItemFilters = InventoryFilters & {
  category?: string
}

export type CreateInventoryCategoryInput = {
  name: string
  description: string
}

export type UpdateInventoryCategoryInput = CreateInventoryCategoryInput

export type CreateInventoryLocationInput = {
  name: string
  description: string
}

export type UpdateInventoryLocationInput = CreateInventoryLocationInput

export type CreateInventoryItemInput = {
  name: string
  category_id: number
  description: string
}

export type UpdateInventoryItemInput = CreateInventoryItemInput
