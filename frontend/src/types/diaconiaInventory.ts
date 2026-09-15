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

export type InventoryCountLocation = {
  location_id: number
  location_name: string
  quantity: number
}

export type InventoryCountItem = {
  item_id: number
  item_name: string
  category_id: number
  category_name: string
  total: number
  locations: InventoryCountLocation[]
}

export type InventoryCount = {
  id: number
  date: string
  notes: string
  created_by: {
    id: number
    display_name: string
  }
  items: InventoryCountItem[]
  created_at: string
  updated_at: string
}

export type InventoryCountListItem = {
  id: number
  date: string
  created_by: {
    id: number
    display_name: string
  }
  items_count: number
  locations_count: number
  created_at: string
  updated_at: string
}

export type InventoryCountFilters = {
  date_from?: string
  date_to?: string
  created_by?: string
}

export type InventoryComparisonStatus = 'INCREASE' | 'DECREASE' | 'UNCHANGED' | 'NEW' | 'NOT_COUNTED'

export type InventoryCountComparisonLocation = {
  location_id: number
  location_name: string
  previous_quantity: number | null
  current_quantity: number | null
  variation: number | null
  status: InventoryComparisonStatus
}

export type InventoryCountComparisonItem = {
  item_id: number
  item_name: string
  category_id: number
  category_name: string
  previous_total: number | null
  current_total: number | null
  variation: number | null
  variation_percent: number | null
  status: InventoryComparisonStatus
  locations: InventoryCountComparisonLocation[]
}

export type InventoryCountComparison = {
  current: {
    id: number
    date: string
    created_at: string
    updated_at: string
  }
  previous: {
    id: number
    date: string
    created_at: string
    updated_at: string
  } | null
  summary: {
    increase: number
    decrease: number
    unchanged: number
    new: number
    not_counted: number
  }
  items: InventoryCountComparisonItem[]
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

export type CreateInventoryCountEntryInput = {
  item_id: number
  location_id: number
  quantity: number
}

export type CreateInventoryCountInput = {
  date: string
  notes: string
  entries: CreateInventoryCountEntryInput[]
}

export type UpdateInventoryCountInput = CreateInventoryCountInput
