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
  stock_status: StockStatus
  stock_status_label: string
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
export type StockStatus = 'NORMAL' | 'LOW_STOCK' | 'WITHOUT_MINIMUM' | 'INACTIVE'

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

export type StockItemFilters = {
  search?: string
  category?: string
  stockStatus?: '' | StockStatus
  status?: 'ACTIVE' | 'INACTIVE' | 'ALL'
}

export type StockMovementFilters = {
  search?: string
  item?: string
  type?: '' | StockMovementType
}

export type StockSummary = {
  active_items: number
  low_stock_items: number
  without_minimum_control: number
  replenishment_items: StockItem[]
}

export type CountingEnvironment = {
  id: number
  name: string
  description: string
  is_active: boolean
  created_at: string
  updated_at: string
}

export type CountingEnvironmentFilters = {
  search?: string
  status?: 'ACTIVE' | 'INACTIVE' | 'ALL'
}

export type CreateCountingEnvironmentInput = {
  name: string
  description: string
}

export type UpdateCountingEnvironmentInput = CreateCountingEnvironmentInput

export type AttendanceShift = 'MORNING' | 'AFTERNOON' | 'EVENING'

export type AttendanceCountEntry = {
  id: number
  environment: Pick<CountingEnvironment, 'id' | 'name' | 'is_active'>
  quantity: number
}

export type AttendanceCount = {
  id: number
  date: string
  shift: AttendanceShift
  shift_label: string
  notes: string
  total_people: number
  created_by: {
    id: number
    display_name: string
  }
  entries: AttendanceCountEntry[]
  created_at: string
  updated_at: string
}

export type CreateAttendanceCountInput = {
  date: string
  shift: AttendanceShift
  notes: string
  entries: Array<{
    environment_id: number
    quantity: number
  }>
}

export type UpdateAttendanceCountInput = CreateAttendanceCountInput

export type AttendanceCountFilters = {
  dateFrom?: string
  dateTo?: string
  shift?: '' | AttendanceShift
  createdBy?: string
}

export type DiaconiaDashboard = {
  stock: {
    active_items: number
    low_stock_items: number
    without_minimum_control: number
    replenishment_items: Array<{
      id: number
      name: string
      category: {
        id: number
        name: string
      }
      unit: string
      unit_label: string
      current_stock: number
      minimum_stock: number
      missing_to_minimum: number
    }>
  }
  attendance: {
    has_data: boolean
    latest: null | {
      id: number
      date: string
      shift: AttendanceShift
      shift_label: string
      total_people: number
      created_by: {
        id: number
        display_name: string
      }
      created_at: string
    }
    previous: null | {
      id: number
      date: string
      shift: AttendanceShift
      shift_label: string
      total_people: number
    }
    comparison: null | {
      previous_total: number
      current_total: number
      variation: number
      variation_percent: number | null
      status: 'INCREASE' | 'DECREASE' | 'UNCHANGED'
    }
    distribution: Array<{
      environment_id: number
      environment_name: string
      quantity: number
    }>
  }
  inventory: {
    has_data: boolean
    latest: null | {
      id: number
      date: string
      created_by: {
        id: number
        display_name: string
      }
      created_at: string
    }
    previous: null | {
      id: number
      date: string
      created_at: string
    }
    summary: null | {
      increase: number
      decrease: number
      unchanged: number
      new: number
      not_counted: number
    }
    reductions: Array<{
      item_id: number
      item_name: string
      category_id: number
      category_name: string
      previous_total: number
      current_total: number
      variation: number
      variation_percent: number | null
    }>
  }
}
